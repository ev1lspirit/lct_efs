import asyncio
from tkinter import W
from api.routes import save_workflow, check_session
from api.schema import SaveWorkflowRequest, WorkflowRequest
from api.tests.integration_workflow_correct_format import get_integration_workflow_with_correct_screens
from api.wf import test_workflow_2_ecommerce_checkout

async def main():
    wf = test_workflow_2_ecommerce_checkout()

    wf_model = SaveWorkflowRequest(**wf, predefined_context={})
    value = await save_workflow(
        body=wf_model
    )
    print(value)

    workflow_id = value["wf_description_id"]
    context_id = value["wf_context_id"]

    resp = await check_session(
        body=WorkflowRequest(
            client_workflow_id=workflow_id, client_session_id=context_id
        )
    )
    print(resp)

if __name__ == "__main__":
    asyncio.run(main())
