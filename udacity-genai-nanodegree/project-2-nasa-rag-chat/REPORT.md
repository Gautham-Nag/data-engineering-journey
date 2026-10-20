# Project Report: NASA Mission Intelligence RAG System

## Summary

The system answers questions about Apollo 11, Apollo 13, and Challenger from 12 NASA text files (5,308 chunks after tuning). It runs end to end: embedding pipeline, semantic search with mission filtering, grounded answers with source citations and conversation memory, real-time RAGAS scoring in the chat app, and batch evaluation over a 7-question test set.

## Challenges and Solutions

**1. RAGAS would not import.**
RAGAS 0.4.3 imports `ChatVertexAI` from an old `langchain-community` path that no longer exists, and the replacement package `langchain-google-vertexai` was not installed in the workspace. I patched the two imports in RAGAS's `llms/base.py` and installed the project requirements. Because a workspace restart resets installed packages, I put both steps in `setup_env.sh` so the environment can be restored with one command.

**2. The model answered from memory when no documents were found.**
In an early test with no context, the model said no documents were found and then answered anyway from general knowledge. I strengthened the system prompt ("never fall back on general knowledge, even for well-known facts") and added an explicit instruction to the question itself when retrieval returns nothing. After this, the model only reports that nothing was found and suggests rephrasing.

**3. Small chunks gave useless context.**
With the default 500-character chunks (16,557 chunks), the question "What problems did Apollo 13 encounter?" retrieved three snippets of routine radio chatter ("Go ahead, Houston", distance updates). The model correctly said the documents did not describe the problems, but the answer was useless. Printing the retrieved chunks showed that 500 characters is only a few lines of transcript. I rebuilt the collection with 1500-character chunks and 300 overlap using `--update-mode replace`, which reduced the collection to 5,308 chunks. The same question then returned a substantive answer about oxygen quantity, power and water conservation, and a display fault in the abort guidance system, with sources cited.

**4. Retrieval mixed up missions.**
Even after re-chunking, one of the top 3 results for an Apollo 13 question came from an Apollo 11 document. I added a mission selector to the chat app, passed to ChromaDB as a metadata filter, and the evaluation dataset sets a mission per question. With the filter on, all results come from the chosen mission.

**5. Chunk ID collisions and repeated runs.**
Several data folders contain files with similar names. Chunk IDs include a short fingerprint of the file path so they never collide, and they stay stable between runs. That stability is what makes `--update-mode skip` resume an interrupted run instead of re-embedding everything.

**6. BLEU and ROUGE needed extra packages.**
The first batch run reported that `sacrebleu` and `rouge_score` were missing. Because each metric runs separately with its own error handling, the other metrics still completed. I installed both packages and added them to `requirements.txt`.

## Evaluation Results

Batch evaluation over 7 questions (1500/300 chunks, 3 retrieved chunks, gpt-3.5-turbo):

| Metric | Mean | Min | Max |
|---|---|---|---|
| Context precision | 0.869 | 0.500 | 1.000 |
| Response relevancy | 0.870 | 0.553 | 1.000 |
| Faithfulness | 0.714 | 0.000 | 1.000 |
| ROUGE | 0.335 | 0.113 | 0.612 |
| BLEU | 0.155 | 0.019 | 0.595 |

**What the numbers say.** Retrieval works well: context precision of 0.87 means the retrieved chunks are usually relevant, and answers stay on topic (relevancy 0.87). Faithfulness is the weak point. The worst case (0.000) was the Apollo 11 timeline question, where the answer included an exact time ("2:56:15 GMT") that was not in the retrieved chunks. The model sometimes adds well-known facts despite the prompt. In live chat I saw the same pattern: the model correctly said the documents did not describe the Apollo 13 oxygen tank explosion, but then mentioned it anyway.

BLEU and ROUGE are low by design. They count exact word overlap with my hand-written expected answers, so a correct answer phrased differently still scores low. They are useful for comparing runs, not as absolute quality measures.

## Possible Improvements

- Retrieve more chunks (k = 5) or add keyword search alongside semantic search, since transcripts often mention key events with specific words such as "oxygen tank" or "O-ring".
- Use a stronger model (gpt-4) for generation, which follows grounding instructions more reliably and should raise faithfulness.
- Add the Apollo 13 and Challenger investigation reports as sources; the current Challenger files are mission audio transcripts, which describe what was heard rather than the cause of the accident.