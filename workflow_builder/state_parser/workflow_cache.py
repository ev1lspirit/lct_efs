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
            from bson import ObjectId
            from bson.errors import InvalidId
            
            logger.debug(f"Attempting to load workflow: {workflow_id}")
            
            # Validate ObjectId format
            try:
                ObjectId(workflow_id)
            except InvalidId:
                logger.error(f"Invalid workflow ID format: {workflow_id}. Must be a valid MongoDB ObjectId (24 hex characters)")
                return None
            
            raw_workflow = self._mongo_client.retrieve_description(workflow_id)
            if not raw_workflow:
                logger.error(f"Workflow {workflow_id} not found in MongoDB collection '{self._mongo_client.collection.name}'")
                logger.info(f"Hint: Make sure the workflow was saved using POST /workflow/save endpoint")
                return None

            # Check if states exist in workflow
            if "states" not in raw_workflow:
                logger.error(f"Workflow {workflow_id} exists but has no 'states' field")
                return None
                
            states_data = raw_workflow.get("states", [])
            if not states_data:
                logger.error(f"Workflow {workflow_id} has empty states array")
                return None

            # Convert raw states to StateModel instances
            states = []
            for idx, raw_state in enumerate(states_data):
                try:
                    state_model = StateModel(**raw_state)
                    states.append(state_model)
                except Exception as state_error:
                    logger.error(f"Error parsing state #{idx} in workflow {workflow_id}: {state_error}")
                    logger.debug(f"Problematic state data: {raw_state}")
                    return None

            logger.info(f"Successfully loaded workflow {workflow_id} with {len(states)} states")
            # Cache the workflow
            self._cache[workflow_id] = states
            return states

        except Exception as e:
            logger.error(f"Unexpected error loading workflow {workflow_id}: {e}", exc_info=True)
            return None

    def invalidate(self, workflow_id: str) -> None:
        """Remove workflow from cache"""
        self._cache.pop(workflow_id, None)


# Global instance
workflow_cache = WorkflowCache()
