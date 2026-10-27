# Win-max plan (user directive Oct 22 ~3:14 IST): optimize entry for winning, honest, <=$25, publish = his call

## What the bar looks like (observed in thread)
- BeamDial: data (2,050 runs) + demo + library + honest limits. Most complete.
- Safety Benchmark: 5 models, 2 suites, live report, independent judge.
- Mada-Bench: benchmark + small synthetic dataset, language angle, $2.3 cost disclosed.

## Our edge
1. Novel question nobody else asked: code-MIXED Hinglish (not low-resource monolingual) on an English-predominant 501B.
2. Personal credibility: his BHASHA Hinglish ASR paper + Voino. Story: "I study Hinglish speech; here's Hinglish understanding in Beam."
3. Two complementary artifacts: GSM8K-Hinglish (established, translated, number-verified) + 100-pair tiered author set.
4. The finding has a hook: accuracy holds, but Hinglish costs ~1.5-2x tokens = real money at scale. "The Hinglish tax."

## Win-max additions (cheap, within budget)
A. Mitigation experiment (~$0.6, 60 gens): on 30 HI items, Beam with "reason in English if easier, output only the number" system prompt -> does the tax shrink? Turns "we found a problem" into "we found a problem AND a fix" = helpful-to-the-world framing judges asked for.
B. Paired qualitative analysis: items where EN right/HI wrong per model - published with per-item predictions.
C. Polished artifacts: dataset card with charts (matplotlib), Space = static leaderboard + per-item explorer + precomputed demo (NO live paid inference on his token; visitors use their own token - documented).
D. Methodology + limits section as rigorous as Mada-Bench's (single run, zero-shot, low effort, 82 items, translation-by-Beam disclosed, 18 exclusions disclosed).
E. Rules-thread comment draft: numbers-forward, 5 lines, links. He posts it (his call).

## Do NOT
- No live API from Space on his token. No paid plan/card. No auto-recharge. No unverifiable claims.
- No spamming the thread; one comment, after his approval.

## Budget ledger (target <= $13 of $25)
- pilot+calibration+translations: ~$4-5.5
- 3-model GSM8K run: ~$3-6
- mitigation experiment: ~$0.6
- contingency reruns: ~$2
- buffer: >= $12 left
