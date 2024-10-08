from typing import Callable

from . import model

Mixin = Callable[[model.Target, model.Tools], model.Tools]


def patchToolArgs(tools: model.Tools, toolSpec: str, args: list[str]):
    tools[toolSpec].args += args


def prefixToolCmd(tools: model.Tools, toolSpec: str, prefix: str):
    tools[toolSpec].cmd = prefix + " " + tools[toolSpec].cmd


def mixinCache(target: model.Target, tools: model.Tools) -> model.Tools:
    prefixToolCmd(tools, "cc", "ccache")
    prefixToolCmd(tools, "cxx", "ccache")
    return tools


def makeMixinSan(san: str) -> Mixin:
    def mixinSan(target: model.Target, tools: model.Tools) -> model.Tools:
        patchToolArgs(tools, "cc", [f"-fsanitize={san}"])
        patchToolArgs(tools, "cxx", [f"-fsanitize={san}"])
        patchToolArgs(tools, "ld", [f"-fsanitize={san}"])

        return tools

    return mixinSan


def makeMixinOptimize(level: str) -> Mixin:
    def mixinOptimize(target: model.Target, tools: model.Tools) -> model.Tools:
        patchToolArgs(tools, "cc", [f"-O{level}"])
        patchToolArgs(tools, "cxx", [f"-O{level}"])

        return tools

    return mixinOptimize


def mixinDebug(target: model.Target, tools: model.Tools) -> model.Tools:
    patchToolArgs(tools, "cc", ["-g", "-gdwarf-4"])
    patchToolArgs(tools, "cxx", ["-g", "-gdwarf-4"])

    return tools


def makeMixinTune(tune: str) -> Mixin:
    def mixinTune(target: model.Target, tools: model.Tools) -> model.Tools:
        patchToolArgs(tools, "cc", [f"-mtune={tune}"])
        patchToolArgs(tools, "cxx", [f"-mtune={tune}"])

        return tools

    return mixinTune


def combineMixins(*mixins: Mixin) -> Mixin:
    def combined(target: model.Target, tools: model.Tools) -> model.Tools:
        for mixin in mixins:
            tools = mixin(target, tools)
        return tools

    return combined


mixins: dict[str, Mixin] = {
    "cache": mixinCache,
    "debug": mixinDebug,
    "asan": combineMixins(makeMixinSan("address"), makeMixinSan("leak")),
    "msan": makeMixinSan("memory"),
    "tsan": makeMixinSan("thread"),
    "ubsan": makeMixinSan("undefined"),
    "lsan": makeMixinSan("leak"),
    "san": combineMixins(
        makeMixinSan("address"),
        makeMixinSan("undefined"),
        makeMixinSan("leak"),
    ),
    "tune": makeMixinTune("native"),
    "release": combineMixins(makeMixinOptimize("3")),
    "o3": makeMixinOptimize("3"),
    "o2": makeMixinOptimize("2"),
    "o1": makeMixinOptimize("1"),
    "o0": makeMixinOptimize("0"),
}


def append(mixinSpec: str, mixin: Mixin):
    mixins[mixinSpec] = mixin


def byId(id: str) -> Mixin:
    if id not in mixins:
        raise RuntimeError(f"Unknown mixin {id}")
    return mixins[id]
