import json
import re

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, StoppingCriteria, StoppingCriteriaList

from core.llm.prompt import build_prompt
from core.llm.verify import verify_analysis


class JsonCloseStoppingCriteria(StoppingCriteria):
    """Stops generation the moment a balanced top-level JSON object closes,
    instead of letting the model keep going until it hits max_new_tokens.

    This turned out to be the actual root cause of everything we were
    fighting: the model doesn't reliably emit an end-of-text token right
    after closing the JSON - it just keeps rambling (which is where the
    repetition loops and duplicate/malformed keys kept coming from).
    Tuning temperature and repetition_penalty was treating the symptom;
    this stops the problem from happening at all.

    Since generation is primed to start with "{" (see generate_raw), we
    count brace depth starting at 1 and stop as soon as it returns to 0.
    """

    def __init__(self, tokenizer, prompt_len):
        self.tokenizer = tokenizer
        self.prompt_len = prompt_len
        self.depth = 1  

    def __call__(self, input_ids, scores, **kwargs):
        new_tokens = input_ids[0][self.prompt_len:]
        if len(new_tokens) == 0:
            return False

        last_token_text = self.tokenizer.decode(new_tokens[-1:], skip_special_tokens=True)

        for ch in last_token_text:
            if ch == "{":
                self.depth += 1
            elif ch == "}":
                self.depth -= 1
                if self.depth == 0:
                    return True
        return False

DEFAULT_MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

_model = None
_tokenizer = None


def load_model(model_name=DEFAULT_MODEL_NAME):
    """Loads the model in 4-bit onto GPU. Only actually loads once per
    process - later calls just hand back what's already loaded, even if
    you pass a different model_name (that'd need a restart to change).
    """
    global _model, _tokenizer

    if _model is not None:
        return _model, _tokenizer

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

    _tokenizer = AutoTokenizer.from_pretrained(model_name)

    if torch.cuda.is_available():
        device_map = {"": 0}
    else:
        device_map = "cpu"

    _model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quant_config,
        device_map=device_map,
    )

    actual_device = next(_model.parameters()).device
    print(f"[generator] model loaded on: {actual_device}")
    if actual_device.type != "cuda" and torch.cuda.is_available():
        print("[generator] WARNING: CUDA is available but the model landed on CPU anyway.")

    return _model, _tokenizer


def extract_json(raw_text):
    """The model is told to respond with only JSON, but small models
    sometimes still wrap it in a markdown fence or add a stray sentence.
    This pulls out the first {...} block it can find rather than
    assuming the whole response is clean JSON.
    """
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if fence_match:
        return fence_match.group(1)

    brace_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if brace_match:
        return brace_match.group(0)

    return raw_text


def generate_raw(prompt, max_new_tokens=350, model_name=DEFAULT_MODEL_NAME, max_context_tokens=4096):
    """Runs the prompt through the model and returns the raw text output.
    Split out from analyze_incident() so it can be tested/swapped without
    dragging the JSON parsing logic along with it.
    """
    model, tokenizer = load_model(model_name)

    messages = [{"role": "user", "content": prompt}]
    prompt_text = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=False
    )
    prompt_text += "{"

    inputs = tokenizer(prompt_text, return_tensors="pt").input_ids

    prompt_tokens = inputs.shape[-1]
    budget_for_input = max_context_tokens - max_new_tokens
    if prompt_tokens > budget_for_input:
        raise ValueError(
            f"Prompt is {prompt_tokens} tokens, but only {budget_for_input} fit "
            f"(model context is {max_context_tokens}, reserving {max_new_tokens} for the "
            f"response). Reduce evidence size - fewer rare templates, shorter KB "
            f"excerpts, or fewer KB hits - and try again."
        )

    inputs = inputs.to(model.device)
    attention_mask = torch.ones_like(inputs)

    stopping_criteria = StoppingCriteriaList([
        JsonCloseStoppingCriteria(tokenizer, prompt_len=inputs.shape[-1])
    ])

    with torch.no_grad():
        output_ids = model.generate(
            inputs,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.2,  
            repetition_penalty=1.1,  
            stopping_criteria=stopping_criteria,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated = output_ids[0][inputs.shape[-1]:]
    return "{" + tokenizer.decode(generated, skip_special_tokens=True)


def repair_truncated_json(text):
    """Attempts to recover a usable object from JSON that got cut off or
    went wrong partway through - which is what kept happening: the model
    writes a valid category/summary/root_cause, then degenerates while
    writing the second field of recommendations (duplicate key, missing
    quote, word-loop). Rather than throw away a response that's almost
    entirely correct, this trims back to the last point the JSON was
    still well-formed and closes it off there.

    Strategy: walk the text character by character tracking bracket
    depth and whether we're inside a string. The moment something looks
    wrong (an unexpected character where a key/value was expected, or we
    run out of input mid-string), cut the text there, trim back to the
    last complete key-value pair, and close every open bracket/brace in
    the correct order. Returns None if nothing usable could be salvaged.
    """
    depth_stack = []
    in_string = False
    escape_next = False
    last_safe_cut = None  

    for i, ch in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue

        if ch in "{[":
            depth_stack.append(ch)
        elif ch in "}]":
            if not depth_stack:
                break  
            opener = depth_stack.pop()
            if (opener == "{" and ch != "}") or (opener == "[" and ch != "]"):
                break  
            if not depth_stack:
                return None
        elif ch == ",":
            last_safe_cut = i

    if last_safe_cut is None:
        return None

    truncated = text[:last_safe_cut]
    closers = {"{": "}", "[": "]"}
    closing = "".join(closers[b] for b in reversed(depth_stack_at(text, last_safe_cut)))

    repaired = truncated + closing
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        return None


def depth_stack_at(text, position):
    """Replays bracket tracking up to a given position - used by
    repair_truncated_json to know exactly what's still open at the cut
    point, so it can close things in the right order.
    """
    depth_stack = []
    in_string = False
    escape_next = False

    for ch in text[:position]:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in "{[":
            depth_stack.append(ch)
        elif ch in "}]":
            if depth_stack:
                depth_stack.pop()

    return depth_stack


def parse_analysis(raw_text):
    """Parses the model's raw output into a dict. Tries a straight parse
    first; if that fails (truncated or malformed JSON - this happened a
    lot during testing with small models rambling past where they should
    have stopped), tries to repair and salvage whatever was still valid
    before things went wrong. Returns None only if nothing could be
    recovered at all.
    """
    json_text = extract_json(raw_text)
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return repair_truncated_json(json_text)


def analyze_incident(evidence, kb_hits, description=None, min_kb_hits=1, model_name=DEFAULT_MODEL_NAME):
    """The main entry point. Takes the evidence object and KB search
    results, builds the prompt, runs the model, and returns a verified
    analysis. If retrieval came back essentially empty, we skip the LLM
    call entirely and return an honest "not enough evidence" result
    instead of letting the model guess - this is FR-25.
    """
    if len(kb_hits) < min_kb_hits:
        return {
            "insufficient_evidence": True,
            "reason": "No relevant knowledge base entries were found for this incident. "
                      "Analysis was not generated to avoid guessing without support.",
        }

    prompt = build_prompt(evidence, kb_hits, description=description)
    raw_output = generate_raw(prompt, model_name=model_name)
    analysis = parse_analysis(raw_output)

    if analysis is None:
        return {
            "insufficient_evidence": False,
            "parse_failed": True,
            "raw_output": raw_output,
            "reason": "The model's response could not be parsed as valid JSON.",
        }

    analysis = verify_analysis(analysis, evidence, kb_hits)
    analysis["insufficient_evidence"] = False
    analysis["parse_failed"] = False
    return analysis
