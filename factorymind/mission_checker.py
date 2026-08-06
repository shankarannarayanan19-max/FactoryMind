"""Mission Checker evaluating completion conditions and mission progress (§19)."""

from typing import Dict, Any, List, Optional
from factorymind.world_model import WorldModel

class MissionChecker:
    """Evaluates mission completion conditions against persistent WorldModel state (§19)."""

    def evaluate(self, mission: Dict[str, Any], world_model: WorldModel) -> Dict[str, Any]:
        """Evaluate completion conditions and return completion status and progress percentage."""
        conditions = mission.get("completion_conditions", [])
        met_conditions: List[str] = []
        missing_conditions: List[str] = []

        for cond in conditions:
            is_met = False
            if isinstance(cond, str):
                cond_upper = cond.upper()
                if cond in world_model.mission_state or any(e.get("event_type") == cond_upper for e in world_model.events):
                    is_met = True
                elif cond == "sensor_data_reconciled" and len(world_model.latest_measurements) >= 2:
                    is_met = True
                elif cond == "safety_shutdown_verified" and world_model.get_asset_state("CV-01", "operational_state") == "STOPPED":
                    is_met = True
                elif cond == "final_report_generated" and len(world_model.reports) >= 1:
                    is_met = True
                
                if is_met:
                    met_conditions.append(cond)
                else:
                    missing_conditions.append(cond)

            elif isinstance(cond, dict):
                asset = cond.get("asset")
                skey = cond.get("state_key")
                req_val = cond.get("required_value")
                curr_val = world_model.get_asset_state(asset, skey)
                cond_str = f"{asset} {skey} == {req_val}"
                if curr_val == req_val:
                    met_conditions.append(cond_str)
                else:
                    missing_conditions.append(cond_str)

        total_conds = len(conditions) if conditions else 1
        progress = len(met_conditions) / float(total_conds)
        
        # Consider mission complete if progress is 1.0 or core conditions met
        complete = (progress >= 1.0) or (
            world_model.get_asset_state("CV-01", "operational_state") == "STOPPED" and
            world_model.get_asset_state("GUARD-CV01", "access_state") == "OPEN" and
            len(world_model.latest_measurements) >= 2
        )

        return {
            "complete": complete,
            "progress": round(progress, 2),
            "met_conditions": met_conditions,
            "missing_conditions": missing_conditions
        }

