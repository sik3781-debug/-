with open("run.py", encoding="cp949") as f: c = f.read()
c = c.replace("load_dotenv()" + chr(39) + "nfrom dotenv import load_dotenv" + chr(39) + "nload_dotenv()", "load_dotenv()")
with open("run.py", "w", encoding="utf-8") as f: f.write(c)
print("완료")
