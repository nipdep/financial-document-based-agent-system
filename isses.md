[Critical]
- missing python packages in the requirements file resulting totally unrelated issues 
- building in memory relational database for test data recording 
- connecting to the services through fix URL in side the code 
  - /src/loader/docx_file.py #line 21
  - /src/doclandler/src/loader/pdf_laoder.py #line 34
- csv and docx loader are using "docling" for some reason, that is not who in [https://github.com/ixd-ai-hub/chatgenie-library/blob/69de93730d943b42841d0a310b6d17ed2f1a6156/chatgenie/loaders/csv.py#L11](original chatgenie library) handled these fiels. 
- there is a dir called `/app/server/file_system.py`, I don't know these kind of named python modules are importable or not. 
- there aren't any dedicated `cgcore/llm` or `cgcore/configs` module to call `lmstudio`, I only see `openai`
  

[Just Bad]
- my god there are so many `src/` directories. To be specific 4, and two of those `src/` dirs are under `src/` dir. And a `source/` dir under `docs/`
- Redudent dir names `agent/`
- And it seem like different functionalities of chatgenie is all over the repo. 
- There is a `Makefile` under `docs/` 
- There is an empty `Dockerfile` in `src/dochandler`