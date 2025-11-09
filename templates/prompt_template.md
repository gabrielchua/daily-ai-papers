Task Description:
Using the details from an AI research paper, produce a JSON object with the keys "category" and "summary".

Category:
- Examine the paper titled "{title}".
- From the list below, choose one category that best represents the paper:
    - Natural Language Processing
    - Computer Vision
    - Reinforcement Learning
    - Machine Learning
    - Multi-Modal
    - Other
- Output only the exact category name with no additional formatting or text.

Summary:
- Write a summary in 4-5 concise sentences covering:
    i. A one-line overall summary.
   ii. The main research question or objective.
  iii. The key methodology.
   iv. Primary results (include at least one quantitative metric).
    v. The main implication for AI practitioners.
- Ensure that your summary is strictly based on the paper’s content and uses technical language.
- If details are missing or unclear, clearly indicate the uncertainty.

Output Requirements:
Return a valid JSON object in this exact format:
{
  "category": "Exact Category Name",
  "summary": "Your summary text..."
}
Do not include markdown formatting or any extra text; the output must be directly parseable (e.g., using json.loads(output)).
