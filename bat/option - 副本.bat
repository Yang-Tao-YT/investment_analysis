#if "%1"=="hide" goto CmdBegin
#start mshta vbscript:createobject("wscript.shell").run("""%~0"" #hide",0)(window.close)&&exit
#:CmdBegin

set PYTHONPATH=F:\BaiduSyncdisk\Í¶×Ê\app\investment_analysis
cd ..
streamlit run streamlitapps/options/options.py --server.port 8501 