from typing import Dict, Optional
from .contract import StateModel
from storage.mongo.client import get_mongo_client
import logging

logger = logging.getLogger(__name__)


class WorkflowCache:
    def __init__(self):
        self._cache: Dict[str, list[StateModel]] = {}
        self._mongo_client = get_mongo_client()

    def get_workflow(self, workflow_id: str) -> Optional[list[StateModel]]:
        """Get workflow from cache or load from MongoDB if not present"""
        if workflow_id in self._cache:
            return self._cache[workflow_id]

        return self._load_workflow(workflow_id)

    def _load_workflow(self, workflow_id: str) -> Optional[list[StateModel]]:
        """Load workflow from MongoDB and cache it"""
        try:
            raw_workflow = self._mongo_client.retrieve_description(workflow_id)
            if not raw_workflow:
                logger.error(f"Workflow {workflow_id} not found in MongoDB")
                return None

            # Convert raw states to StateModel instances
            states = []
            for raw_state in raw_workflow.get("states", []):
                state_model = StateModel(**raw_state)
                states.append(state_model)

            # Cache the workflow
            self._cache[workflow_id] = states
            return states

        except Exception as e:
            logger.error(f"Error loading workflow {workflow_id}: {e}")
            return None

    def invalidate(self, workflow_id: str) -> None:
        """Remove workflow from cache"""
        self._cache.pop(workflow_id, None)


# Global instance
workflow_cache = WorkflowCache()
