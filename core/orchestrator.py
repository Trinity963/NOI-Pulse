# core/orchestrator.py
import logging
class Orchestrator:
    def __init__(self):
        self.nodes = []
        
    def _init_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] [MiniTrini] %(levelname)s: %(message)s",
        )
        logging.info("Orchestrator initialized.")

    def add_node(self, node):
        self.nodes.append(node)

    def run(self, context):
        self._init_logging()
        logging.info("Orchestrator run started.")    
        for node in self.nodes:
            result = node.run(context)
            if result is None:
                break
            context = result
            logging.info("Orchestrator run completed.")
        return context
