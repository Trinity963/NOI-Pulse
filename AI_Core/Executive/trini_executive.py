import json
from pathlib import Path
from datetime import datetime

class TriniExecutive:

    def __init__(self, project_root):
        self.path = Path(project_root) / "AI_Core" / "Executive" / "goals.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self.path.write_text("[]")

        self.goals = self._load()

    def _load(self):
        return json.loads(self.path.read_text())

    def _save(self):
        self.path.write_text(json.dumps(self.goals, indent=2))

    def add_goal(self, objective):
        goal_id = f"goal_{len(self.goals)+1:03d}"
        goal = {
            "id": goal_id,
            "objective": objective,
            "status": "active",
            "priority": 3,  # 1 = critical, 5 = low
            "autonomy_level": 2,  # 0 = manual, 3 = full autonomous
            "progress_log": [],
            "cycle_count": 0,
            "last_update": datetime.utcnow().isoformat()
        }
        self.goals.append(goal)
        self._save()
        return goal

    def update_goal(self, goal_id, update_text):
        for goal in self.goals:
            if goal["id"] == goal_id:
                goal["progress_log"].append(update_text)
                goal["last_update"] = datetime.utcnow().isoformat()
                goal["cycle_count"] = goal.get("cycle_count", 0) + 1
                self._save()
                return

    def bump_cycle(self, goal_id):
        for goal in self.goals:
            if goal["id"] == goal_id:
                goal["cycle_count"] = goal.get("cycle_count", 0) + 1
                goal["last_update"] = datetime.utcnow().isoformat()
                self._save()
                return

    def get_active_goals(self):
        return sorted(
            [g for g in self.goals if g["status"] == "active"],
            key=lambda g: g.get("priority", 3)
        )

    def complete_goal(self, goal_id):
        for goal in self.goals:
            if goal["id"] == goal_id:
                goal["status"] = "complete"
                self._save()
                
                
    def should_run(self, goal, cooldown_seconds=120):
        from datetime import datetime
        last = datetime.fromisoformat(goal["last_update"])
        delta = (datetime.utcnow() - last).total_seconds()
        return delta > cooldown_seconds                