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
    
    def get_pointer_address(self, base_address, offsets):
        address = base_address
        for offset in offsets:
            address = self.pm.read_int(address) + offset
        return address
    

if __name__ == "__main__":
    memory_reader = MemoryReader()
    print(memory_reader.base_address)
    print(memory_reader.fmod_base)

