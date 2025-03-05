import pymem


class MemoryReader:
    def __init__(self):
        self.pm = pymem.Pymem("WoW.exe")
        self.base_address = self.get_module_base("Wow.exe")
        self.fmod_base = self.get_module_base("fmod.dll")

    # 获取模块基址
    def get_module_base(self, module_name):
        modules = self.pm.list_modules()
        for module in modules:
            if module_name.lower() in module.name.lower():
                return module.lpBaseOfDll
    

