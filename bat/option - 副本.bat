#if "%1"=="hide" goto CmdBegin
#start mshta vbscript:createobject("wscript.shell").run("""%~0"" #hide",0)(window.close)&&exit
#:CmdBegin

set PYTHONPATH=$PYTHONPATH:F:\BaiduSyncdisk\投资\app\investment_analysis\strategy\
cd ..
streamlit run streamlitapps/options/options.py --server.port 8501 