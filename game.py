#!/usr/bin/env python3
"""
Chronicle - 文字冒险游戏引擎
玩家通过选择推进剧情，状态自动存档
"""
import json, os, sys
from datetime import datetime

GAME_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(GAME_DIR, "save.json")
STORY_FILE = os.path.join(GAME_DIR, "story.json")

# ─── 引擎 ───────────────────────────────────────────

def load_story():
    with open(STORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_save():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_game(state):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def new_game():
    story = load_story()
    start = story["start"]
    state = {
        "chapter": start,
        "flags": {},
        "inventory": [],
        "history": []
    }
    save_game(state)
    return state, story

def continue_game():
    story = load_story()
    state = load_save()
    return state, story

# ─── 渲染 ───────────────────────────────────────────

def render(story, state):
    node = story["chapters"][state["chapter"]]
    lines = []

    # 章节标题
    if "title" in node:
        lines.append(f"\n═══ {node['title']} ═══\n")

    # 叙述文本
    if "text" in node:
        lines.append(node["text"])

    # 选项
    if "choices" in node:
        lines.append("")
        for i, c in enumerate(node["choices"], 1):
            lines.append(f"  [{i}] {c['text']}")

    # 状态栏
    if "inventory_show" in node:
        inv = state.get("inventory", [])
        if inv:
            lines.append(f"\n📦 持有: {', '.join(inv)}")

    return "\n".join(lines)

def make_choice(story, state, idx):
    node = story["chapters"][state["chapter"]]
    choices = node.get("choices", [])

    if idx < 1 or idx > len(choices):
        return "无效选择。", False

    choice = choices[idx - 1]
    ch = choice.get("chapter")
    effect = choice.get("effect", {})

    # 应用效果
    if "set_flag" in effect:
        state["flags"].update(effect["set_flag"])
    if "clear_flag" in effect:
        for k in effect["clear_flag"]:
            state["flags"].pop(k, None)
    if "add_item" in effect:
        for item in effect["add_item"]:
            if item not in state["inventory"]:
                state["inventory"].append(item)
    if "remove_item" in effect:
        for item in effect["remove_item"]:
            if item in state["inventory"]:
                state["inventory"].remove(item)

    # 跳转章节
    if ch:
        state["chapter"] = ch

    # 特殊：结束
    if "ending" in effect:
        state["ended"] = True

    save_game(state)
    return None, effect.get("ending") == True

# ─── REPL ──────────────────────────────────────────

def repl():
    print("╔══════════════════════════════════╗")
    print("║       Chronicle · 编年史          ║")
    print("╚══════════════════════════════════╝\n")

    save = load_save()
    if save:
        print("  [1] 继续游戏")
    print("  [2] 新游戏")
    if save:
        print("  [3] 删除存档并重新开始")
    print("")

    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            return

        if save and cmd == "1":
            state, story = continue_game()
            break
        elif cmd == "2":
            state, story = new_game()
            break
        elif save and cmd == "3":
            os.remove(SAVE_FILE)
            print("存档已删除。\n")
            save = None
            continue
        else:
            print("请输入有效选项。")
            continue

    print(render(story, state))

    while True:
        try:
            cmd = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            save_game(state)
            print("\n已存档，再见。")
            return

        if cmd in ("q", "quit", "exit"):
            save_game(state)
            print("已存档。")
            return

        if not cmd.isdigit():
            print("请输入选项数字。")
            print(render(story, state))
            continue

        err, ended = make_choice(story, state, int(cmd))
        if err:
            print(err)
            continue

        output = render(story, state)
        print(output)

        if ended:
            print("\n—— THE END ——")
            print("输入任意键退出。")
            try: input()
            except: pass
            return

if __name__ == "__main__":
    repl()
