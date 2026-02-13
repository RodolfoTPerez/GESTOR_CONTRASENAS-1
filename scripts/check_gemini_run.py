from src.infrastructure.gemini_ai import GeminiAI

if __name__ == '__main__':
    report = {'score':50,'status':'Riesgoso','stats':{'total':2},'findings':[{'type':'warning','title':'Test','desc':'Desc'}]}
    g = GeminiAI()
    print('enabled=', g.enabled)
    try:
        out = g.analyze_vulnerabilities(report)
        print('analyze_vulnerabilities output:\n', out)
    except Exception as e:
        print('exception calling analyze:', e)
