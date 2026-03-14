import os
import re


class EditTool:
    @staticmethod
    def edit(file_path: str, edit_content: str) -> str:
        """
        Applies a unified diff edit to a file.
        Returns the new content of the file.
        """
        if not os.path.exists(file_path):
            content = []
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.readlines()

        edit_lines = edit_content.splitlines(keepends=True)
        hunk_re = re.compile(r"^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@")

        hunks = []
        current_hunk = None

        for line in edit_lines:
            if line.startswith("---") or line.startswith("+++"):
                continue

            match = hunk_re.match(line)
            if match:
                if current_hunk:
                    hunks.append(current_hunk)
                current_hunk = {
                    "start_old": int(match.group(1)),
                    "len_old": int(match.group(2) or 1),
                    "start_new": int(match.group(3)),
                    "len_new": int(match.group(4) or 1),
                    "lines": [],
                }
            elif current_hunk:
                current_hunk["lines"].append(line)

        if current_hunk:
            hunks.append(current_hunk)

        result_lines = list(content)
        offset = 0

        for hunk in hunks:
            start_in_file = hunk["start_old"] - 1 + offset
            old_len = hunk["len_old"]

            new_hunk_lines = []
            for h_line in hunk["lines"]:
                if h_line.startswith(" "):
                    new_hunk_lines.append(h_line[1:])
                elif h_line.startswith("+"):
                    new_hunk_lines.append(h_line[1:])
                elif h_line.startswith("-"):
                    pass

            # Pad result_lines if the edit references lines beyond current EOF
            while len(result_lines) < start_in_file:
                result_lines.append("\n")

            result_lines[start_in_file : start_in_file + old_len] = new_hunk_lines
            offset += len(new_hunk_lines) - old_len

        return "".join(result_lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3:
        path, edit_file = sys.argv[1], sys.argv[2]
        with open(edit_file, "r") as pf:
            edit = pf.read()
        new_text = EditTool.edit(path, edit)
        with open(path, "w") as f:
            f.write(new_text)
        print(f"Applied edit to {path}")
