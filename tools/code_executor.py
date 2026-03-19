# tools/code_executor.py
import os
import subprocess
import sqlite3
from config.settings import DIRS

class CodeInjectionTester:
    def __init__(self):
        self.sandbox_dir = DIRS["sandbox"]
        self.blacklist_py = ["os.remove", "shutil.rmtree", "powershell", "format", "shutdown", "subprocess", "sys.exit"]
        self.blacklist_js = ["fs.unlink", "child_process", "process.exit", "rmSync"]
        self.blacklist_sh = ["rm -rf", "format", "del /s", "rmdir"]

    def test_code(self, code_str, language="python"):
        temp_file = "" 
        try:
            if language == "python":
                for w in self.blacklist_py:
                    if w in code_str: return f"❌ Bloqueado: '{w}'."
                
                import io
                from contextlib import redirect_stdout
                f = io.StringIO()
                try:
                    with redirect_stdout(f):
                        exec(code_str, {'__builtins__': __builtins__}, {})
                    saida = f.getvalue()
                    return f"✅ Saída RAM (Fileless):\n{saida.strip()}" if saida else "✅ Execução em memória limpa."
                except Exception as e:
                    return f"❌ Erro na RAM (Python): {e}"

            elif language == "javascript":
                for w in self.blacklist_js:
                    if w in code_str: return f"❌ Bloqueado: '{w}'."
                cmd = ["node"]
                result = subprocess.run(cmd, input=code_str, capture_output=True, text=True, timeout=10)
                output = result.stdout if result.returncode == 0 else result.stderr
                return f"✅ Saída Sandbox JS:\n{output.strip()}" if output else "✅ Execução JS finalizada sem saída."

            elif language == "shell":
                for w in self.blacklist_sh:
                    if w in code_str: return f"❌ Bloqueado: '{w}'."
                ext = ".bat" if os.name == "nt" else ".sh"
                temp_file = os.path.join(self.sandbox_dir, f"temp_exec{ext}")
                with open(temp_file, "w", encoding="utf-8") as f: f.write(code_str)
                cmd = [temp_file] if os.name == 'nt' else ["bash", temp_file]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                output = result.stdout if result.returncode == 0 else result.stderr
                return f"✅ Saída Sandbox Shell:\n{output.strip()}" if output else "✅ Execução Shell finalizada."

            elif language == "sql":
                conn = sqlite3.connect(os.path.join(self.sandbox_dir, "aurora_lab.db"))
                cursor = conn.cursor()
                if code_str.strip().upper().startswith("SELECT"):
                    cursor.execute(code_str)
                    header = [desc[0] for desc in cursor.description]
                    saida = f"COLUNAS: {header}\nRESULTADOS: {cursor.fetchall()}"
                else:
                    cursor.execute(code_str)
                    conn.commit()
                    saida = f"SQL executado. Linhas: {cursor.rowcount}"
                conn.close()
                return f"✅ Saída SQL:\n{saida}"
            
            else: 
                return "❌ Linguagem não suportada."

        except subprocess.TimeoutExpired: return "❌ Timeout estourado."
        except Exception as e: return f"❌ Erro Sandbox: {e}"
        finally:
            if temp_file and os.path.exists(temp_file):
                try: os.remove(temp_file)
                except: pass

# Instância global para ser importada
sandbox_tester = CodeInjectionTester()