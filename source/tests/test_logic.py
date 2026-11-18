import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent_backend import DB, TOPICS, search_notes, safe_progress, tool_run, run_agent


class DataTests(unittest.TestCase):
    def test_course_chapters_and_unique_questions(self):
        self.assertEqual(len(DB['topics']),10)
        self.assertEqual(set(TOPICS),{'1.1','1.2','1.3','1.4','2.1','2.2','2.3','2.4','2.5','2.6'})
        ids=[]
        for topic in DB['topics']:
            for q in topic['questions']:
                ids.append(q['id'])
                self.assertTrue(q['prompt'])
                self.assertTrue(q['why'])
                self.assertEqual(len(q['options']),4)
                self.assertIn(q['answer'],range(4))
        self.assertEqual(len(ids),len(set(ids)))
        self.assertGreaterEqual(len(ids),20)

    def test_retrieval_finds_rag(self):
        self.assertEqual(search_notes('RAG 和微调')[0]['topic_id'],'1.4')

    def test_progress_sanitizing(self):
        self.assertEqual(safe_progress({'1.4':{'attempts':5,'correct':6}},'1.4')['correct'],5)
        self.assertEqual(safe_progress({},'1.2')['accuracy'],None)

    def test_question_selection(self):
        response=tool_run('select_practice',{'topic_id':'1.4'},{})
        self.assertEqual(response['topic_id'],'1.4')
        self.assertNotIn('answer',response)

    def test_real_agent_tool_call_mock(self):
        calls=[]
        def fake_model(messages):
            calls.append(messages)
            if len(calls)==1:
                return {'role':'assistant','tool_calls':[{'id':'call1','type':'function','function':{'name':'search_notes','arguments':'{"query":"RAG"}'}}]}
            return {'role':'assistant','content':'根据演示知识卡，RAG在推理时使用检索材料。'}
        response=run_agent('RAG 是什么',{},'1.4',completion=fake_model)
        self.assertEqual(len(response['tool_calls']),1)
        self.assertEqual(response['tool_calls'][0]['name'],'search_notes')
        self.assertTrue(response['model_used'])
        self.assertIn('RAG',response['answer'])


if __name__=='__main__':
    unittest.main()
