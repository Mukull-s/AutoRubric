import httpx
import time

def run_test():
    client = httpx.Client(base_url='http://localhost:8000')
    
    # 1. Login
    auth = client.post('/auth/login', data={'username': 'admin@example.com', 'password': 'admin'}).json()
    token = auth.get('access_token')
    if not token:
        print("Login failed:", auth)
        return
    headers = {'Authorization': f'Bearer {token}'}
    print("1. Logged in successfully.")

    # 2. Create custom rubric
    new_rubric = {
        'title': 'Photosynthesis Assessment',
        'criteria': [
            {'id': 'c1', 'description': 'Explains that plants absorb sunlight and use chloroplasts', 'weight': 2.0, 'depends_on': []},
            {'id': 'c2', 'description': 'Mentions production of glucose and oxygen', 'weight': 2.0, 'depends_on': ['c1']}
        ]
    }
    r_res = client.post('/rubrics', json=new_rubric, headers=headers).json()
    rubric_id = r_res['id']
    print(f"2. Created dynamic rubric ID: {rubric_id} - '{r_res['title']}'")

    # 3. Submit PDF
    pdf_path = 'tests/fixtures/extraction/clean_single_column.pdf'
    with open(pdf_path, 'rb') as f:
        files = {'file': ('test_submission.pdf', f.read(), 'application/pdf')}
        sub_res = client.post('/submissions', data={'rubric_id': rubric_id}, files=files, headers=headers).json()

    job_id = sub_res['job_id']
    print(f"3. Uploaded submission! Job ID: {job_id}")

    # 4. Poll job status
    final_status = "QUEUED"
    doc_id = None
    for i in range(12):
        time.sleep(1)
        j_res = client.get(f'/jobs/{job_id}', headers=headers).json()
        final_status = j_res.get('status')
        doc_id = j_res.get('doc_id')
        print(f"   Poll {i+1}: status={final_status}, doc_id={doc_id}")
        if final_status in ('DONE', 'NEEDS_REVIEW', 'FAILED'):
            break

    # 5. Fetch result
    if doc_id and final_status in ('DONE', 'NEEDS_REVIEW'):
        res = client.get(f'/results/{doc_id}', headers=headers)
        if res.status_code == 200:
            result = res.json()
            print("\n=== GRADING COMPLETED SUCCESSFULLY! ===")
            print(f"Total Score: {result.get('total')} / {result.get('max_total')}")
            for c in result.get('per_criterion', []):
                print(f" - Criterion {c['criterion_id']}: {c['label']} | Marks: {c['marks']} | BBoxes: {len(c.get('evidence_bboxes', []))} boxes")
            print(f"Annotated PDF available: {result.get('annotated_pdf_available')}")
        else:
            print("Failed to fetch result:", res.status_code, res.text)
    else:
        print("Job did not complete in time:", final_status)

if __name__ == '__main__':
    run_test()
