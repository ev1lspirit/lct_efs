import asyncio
from tkinter import W
import uuid
from api.routes import save_workflow, check_session
from api.schema import SaveWorkflowRequest, WorkflowRequest
from api.tests.integration_workflow_correct_format import get_integration_workflow_with_correct_screens
from api.wf import test_workflow_2_ecommerce_checkout

async def main():
    wf = test_workflow_2_ecommerce_checkout()

    # wf_model = SaveWorkflowRequest(**wf, predefined_context={})
    # value = await save_workflow(
    #     body=wf_model
    # )
    # print(value)

    workflow_id = "68f3a0c307b22181da006c39"
    client_session_id = uuid.uuid4()

    resp = await check_session(
        body=WorkflowRequest(
            client_workflow_id=workflow_id,
            client_session_id=str(client_session_id),
            context={"card_items": [{"id": "123", "price": 100}]},
        )
    )
    print(resp)

if __name__ == "__main__":
    asyncio.run(main())
