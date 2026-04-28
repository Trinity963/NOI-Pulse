class InferenceBackend:
    name = "base"

    def load(self, model_path, config):
        raise NotImplementedError

    def generate(self, prompt, stream=False):
        raise NotImplementedError

    def unload(self):
        pass
