# -*- coding: utf-8 -*-
"""Portfolio 01: reproducible synthetic financial scenario, XLSX & PDF output."""
from __future__ import annotations
import random, math, json, csv, os, statistics, collections
from pathlib import Path
from datetime import datetime
BASE=Path('/mnt/data'); RNG=random.Random(20261011)
YEAR=2025
DEPTS=[('IT','IT導入支援',20),('BPO','業務アウトソーシング',15),('TRN','企業研修・人材育成',10),('HQ','本社管理',5)]
CUSTOMERS=[]
for i in range(1,46):
    dept='IT' if i<=18 else 'BPO' if i<=33 else 'TRN'
    size='大企業' if i in [1,2,3,19,20,34] else ('中堅企業' if i%3 else '中小企業')
    package='継続契約' if (dept=='BPO' or i%5!=0) else 'スポット中心'
    CUSTOMERS.append({'id':f'C{i:03}', 'name':f'架空法人顧客 {i:03}', 'dept':dept,'segment':size,'contract':package,'region':('関東','関西','中部','九州・四国')[i%4]})
season={'IT':[.91, .97,1.05,1.02,1.03,1.00,1.00,.98,1.07,1.11,1.05,1.17],
        'BPO':[.95,.95,.99,1.0,1.03,1.01,1.02,1.03,1.02,1.03,1.03,1.01],
        'TRN':[.91,.91,1.22,1.10,1.12,.90,.66,.64,.80,1.2,1.19,1.18]}
TX=[]
for m in range(1,13):
    for i,c in enumerate(CUSTOMERS,1):
        d=c['dept']
        probability={'IT':.82,'BPO':.94,'TRN':.79}[d]
        if c['contract']=='スポット中心': probability*=.69
        if RNG.random() > probability: continue
        if d=='IT':
            size_multiplier={1:4.5,2:3.2,3:2.3}.get(i,1.0)
            amount=RNG.uniform(0.85,1.65)*1_000_000*size_multiplier
            service='導入・運用支援'
        elif d=='BPO':
            size_multiplier={19:2.4,20:1.8}.get(i,1.0)
            amount=RNG.uniform(.95,1.6)*1_000_000*size_multiplier
            service='業務運用代行'
        else:
            size_multiplier={34:1.6}.get(i,1.0)
            amount=RNG.uniform(.60,1.32)*1_000_000*size_multiplier
            service='研修プログラム'
        n=1+(RNG.random() < {'IT':.50,'BPO':.30,'TRN':.34}[d])
        for j in range(int(n)):
            revenue=round(amount*season[d][m-1]*(RNG.uniform(.32,.58) if n==2 else 1)/1000)*1000
            if d=='IT': rate=RNG.uniform(.29,.41)
            elif d=='BPO': rate=RNG.uniform(.21,.29)+(.14 if m>=10 else (.06 if m>=7 else 0))
            else: rate=RNG.uniform(.10,.23)
            rate=max(0.08,min(0.65,rate))
            direct=round(revenue*rate/1000)*1000
            if d=='IT': splits=[.55,.35,.10]
            elif d=='BPO': splits=[.76,.13,.11]
            else: splits=[.36,.18,.46]
            costs=[round(direct*splits[0]/1000)*1000,round(direct*splits[1]/1000)*1000]
            costs.append(direct-sum(costs))
            TX.append({'tx_id':f'T{len(TX)+1:04}', 'month':m,'customer':c['id'],'dept':d,'quarter':f'Q{(m-1)//3+1}',
                       'contract':c['contract'], 'service':service,'revenue':revenue,'outsourcing':costs[0],
                       'license':costs[1], 'otherdirect':costs[2],'variable':direct,'contrib':revenue-direct})
COSTS=[]
for m in range(1,13):
    for d,name,head in DEPTS:
        payroll={'IT':11_500_000,'BPO':8_450_000,'TRN':5_250_000,'HQ':3_400_000}[d]
        overhead={'IT':1_720_000,'BPO':1_380_000,'TRN':930_000,'HQ':1_150_000}[d]
        # Extra overtime/personnel costs in BPO Q4, a constructed management scenario.
        if d=='BPO' and m>=10: payroll+=650_000
        payroll=round(payroll*(1+(m-1)*.0015)/1000)*1000
        COSTS.append({'month':m,'quarter':f'Q{(m-1)//3+1}', 'dept':d,'payroll':payroll,'overhead':overhead,'total':payroll+overhead})
BUDGET=[]
for m in range(1,13):
    for d,name,head in DEPTS[:3]:
        rev_base={'IT':27_000_000,'BPO':21_000_000,'TRN':9_700_000}[d]
        sf={'IT':[.95,.95,1.04,1.02,1.03,1.00,1.0,1.0,1.07,1.09,1.09,1.15],
            'BPO':[1.00]*12,
            'TRN':[.9,.9,1.18,1.10,1.11,.94,.97,.99,1.04,1.16,1.16,1.14]}[d][m-1]
        rev=round(rev_base*sf/1000)*1000
        cost_rate={'IT':.35,'BPO':.26,'TRN':.17}[d]
        # Budget-side fixed cost assumptions independent of actuals.
        divcost={'IT':13_150_000,'BPO':9_850_000,'TRN':6_150_000}[d]
        hqcost=4_550_000*head/45
        variable=round(rev*cost_rate/1000)*1000
        hqalloc=round(hqcost/1000)*1000
        prof=rev-variable-divcost-hqalloc
        BUDGET.append({'month':m,'quarter':f'Q{(m-1)//3+1}','dept':d,'rev':rev,'rate':cost_rate,'variable':variable,
                       'deptcost':divcost,'hqcost':hqalloc,'op_budget':prof})

def summarize():
    by_mdept={}; by_dept={}; by_cust={}
    for t in TX:
        k=(t['month'],t['dept']); d=by_mdept.setdefault(k,{'revenue':0,'variable':0,'contribution':0})
        d['revenue']+=t['revenue']; d['variable']+=t['variable'];d['contribution']+=t['contrib']
        c=by_cust.setdefault(t['customer'],{'revenue':0,'contrib':0});c['revenue']+=t['revenue'];c['contrib']+=t['contrib']
    analysis=[]
    for m in range(1,13):
        for code,name,head in DEPTS[:3]:
            a=by_mdept.get((m,code),{'revenue':0,'variable':0,'contribution':0})
            deptcost=next(z['total'] for z in COSTS if z['month']==m and z['dept']==code)
            hqcost=next(z['total'] for z in COSTS if z['month']==m and z['dept']=='HQ')
            alloc=(hqcost-round(hqcost*20/45)-round(hqcost*15/45)) if code=='TRN' else round(hqcost*head/45)
            bud=next(z for z in BUDGET if z['month']==m and z['dept']==code)
            row={'month':m,'quarter':f'Q{(m-1)//3+1}','dept':code,**a, 'department_cost':deptcost, 'hq_alloc':alloc,
                 'profit':a['contribution']-deptcost-alloc,'budget':bud['rev'],'profit_budget':bud['op_budget']}
            analysis.append(row)
    revenue=sum(r['revenue'] for r in analysis); variable=sum(r['variable'] for r in analysis)
    prof=sum(r['profit'] for r in analysis); budget=sum(r['budget'] for r in analysis)
    assert revenue==sum(t['revenue'] for t in TX)
    assert variable==sum(t['variable'] for t in TX)
    assert all(t['revenue']==t['contrib']+sum(t[z] for z in ['outsourcing','license','otherdirect']) for t in TX)
    assert sum(r['department_cost'] for r in analysis)==sum(x['total'] for x in COSTS if x['dept']!='HQ')
    # Largest remainder allocation may differ by +- 1 JPY per month, so ensure it is exact via distribution.
    assert sum(r['hq_alloc'] for r in analysis)==sum(x['total'] for x in COSTS if x['dept']=='HQ')
    assert prof==revenue-variable-sum(c['total'] for c in COSTS)
    bydept={d:{'revenue':sum(a['revenue'] for a in analysis if a['dept']==d),
               'profit':sum(a['profit'] for a in analysis if a['dept']==d),
               'budget':sum(a['budget'] for a in analysis if a['dept']==d)} for d in ['IT','BPO','TRN']}
    byquarter={f'Q{q}':{'revenue':sum(a['revenue'] for a in analysis if a['quarter']==f'Q{q}'),
                         'profit':sum(a['profit'] for a in analysis if a['quarter']==f'Q{q}')} for q in range(1,5)}
    top=sorted(by_cust.items(), key=lambda kv:kv[1]['revenue'],reverse=True)
    return {'revenue':revenue,'variable':variable,'profit':prof,'budget':budget,
            'margin':prof/revenue,'achievement':revenue/budget,'analysis':analysis,
            'bydept':bydept,'byquarter':byquarter,'bycustomer':by_cust,
            'top_customers':top[:8], 'top5_share':sum(x[1]['revenue'] for x in top[:5])/revenue,
            'n_tx':len(TX),'n_customers':len(CUSTOMERS)}
assert len(TX)==len(set(x['tx_id'] for x in TX))
assert all(x['customer'] in {c['id'] for c in CUSTOMERS} for x in TX)
assert all(x['dept']==next(c['dept'] for c in CUSTOMERS if c['id']==x['customer']) for x in TX)
assert all(x['variable']>=0 and x['revenue']>=x['variable'] for x in TX)
SUMMARY=summarize()
(BASE/'portfolio01_metrics.json').write_text(json.dumps({k:v for k,v in SUMMARY.items() if k not in ['analysis','bycustomer','top_customers']},ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':
    print('transactions=',len(TX))
    print('revenue=',SUMMARY['revenue'],'profit=',SUMMARY['profit'],'margin=',SUMMARY['margin'],'achievement=',SUMMARY['achievement'])
    print('divisions=',SUMMARY['bydept'],'quarters=',SUMMARY['byquarter'],'top5 share=',SUMMARY['top5_share'])

NAVY='#142B46'; BLUE='#1E466B'; TEAL='#087E8B'; PALE='#E8F3F4'; INK='#172B43'; MUTED='#60758A'; WHITE='#FFFFFF'; INPUT='#214DCE'; GREEN='#087A45'; RED='#C03944'; LT='#F4F7FB'
YEN='#,##0;[Red](#,##0);-'; MM='#,##0.0;[Red](#,##0.0);-'; PCT='0.0%;[Red](0.0%);-'

def make_workbook():
    from artifact_tool import Workbook, SpreadsheetFile
    wb=Workbook.create()
    names=['Dashboard','Transactions','Customers','Divisions','Budget','MonthlyCosts','Analysis','Validation','Guide_AI_Log']
    ss={name:wb.worksheets.add(name) for name in names}
    def section(sh,a,b,text):
        sh.merge_cells(f'{a}:{b}'); first=a.split(':')[0]
        sh.get_range(first).values=[[text]]
        sh.get_range(f'{a}:{b}').format={'fill':NAVY,'font':{'color':WHITE,'bold':True,'size':11},'row_height':27,'vertical_alignment':'center'}
    def header(sh,address):
        sh.get_range(address).format={'fill':BLUE,'font':{'color':WHITE,'bold':True,'size':10},'row_height':26,'vertical_alignment':'center','wrap_text':True}
    def title(sh,label,last='M'):
        sh.merge_cells(f'A1:{last}2'); sh.get_range('A1').values=[[label]]
        sh.get_range(f'A1:{last}2').format={'fill':NAVY,'font':{'color':WHITE,'bold':True,'size':19},'row_height':25,'vertical_alignment':'center'}
    def setwidth(sh,addr,width): sh.get_range(addr).format.column_width=width
    # Divisions
    sh=ss['Divisions'];sh.get_range('A1:E5').values=[['部門ID','部門名','人員数（名）','本社共通費配賦率','区分']]+[[d,n,h,None,('共通' if d=='HQ' else '事業') ] for d,n,h in DEPTS]
    sh.get_range('D2:D4').formulas=[[f'=C{r}/SUM($C$2:$C$4)'] for r in range(2,5)]
    sh.get_range('D5').values=[[0]]
    header(sh,'A1:E1');setwidth(sh,'A:A',14);setwidth(sh,'B:B',31);setwidth(sh,'C:E',20)
    sh.get_range('D2:D5').set_number_format(PCT);sh.get_range('C2:C5').format.font.color=INPUT
    sh.get_range('A7:E8').values=[['共通費配賦方式','事業部45名の人員比率。HQ5名は配賦対象に含まない。',None,None,None],
                                 ['二重計上防止','社員の人件費はMonthlyCostsのみ。Transactions直接費には計上しない。',None,None,None]]
    # Transactions
    sh=ss['Transactions'];headers=['取引ID','月','顧客ID','部門ID','四半期','契約区分','サービス','売上高（円）','外注費（円）','ライセンス費（円）','その他変動費（円）','変動費計（円）','限界利益（円）']
    raw=[[x['tx_id'],x['month'],x['customer'],x['dept'],x['quarter'],x['contract'],x['service'],x['revenue'],x['outsourcing'],x['license'],x['otherdirect'],None,None] for x in TX]
    sh.get_range(f'A1:M{len(raw)+1}').values=[headers]+raw
    sh.get_range(f'L2:M{len(raw)+1}').formulas=[[f'=SUM(I{r}:K{r})',f'=H{r}-L{r}'] for r in range(2,len(raw)+2)]
    header(sh,'A1:M1');sh.freeze_panes.freeze_rows(1)
    setwidth(sh,'A:A',13);setwidth(sh,'B:E',12);setwidth(sh,'F:G',19);setwidth(sh,'H:M',20)
    sh.get_range(f'H2:M{len(raw)+1}').set_number_format(YEN)
    sh.get_range(f'H2:K{len(raw)+1}').format.font.color=INPUT
    # Customers: H selected revenue, I contribution, J current share
    sh=ss['Customers'];heads=['顧客ID','顧客名（完全架空）','主担当部門','顧客区分','契約形態','地域','備考','選択期間売上（円）','選択期間限界利益（円）','売上構成比']
    sh.get_range('A1:J46').values=[heads]+[[x['id'],x['name'],x['dept'],x['segment'],x['contract'],x['region'],'',None,None,None] for x in CUSTOMERS]
    cust_forms=[]
    for r in range(2,47):
        dept=f'IF(AND(Dashboard!$B$4<>"全部門",C{r}<>Dashboard!$B$4),0,'
        cust_forms.append([
            f'={dept}IF(Dashboard!$L$4="通期",SUMIF(Transactions!$C$2:$C$2000,A{r},Transactions!$H$2:$H$2000),SUMIFS(Transactions!$H$2:$H$2000,Transactions!$C$2:$C$2000,A{r},Transactions!$E$2:$E$2000,Dashboard!$L$4)))',
            f'={dept}IF(Dashboard!$L$4="通期",SUMIF(Transactions!$C$2:$C$2000,A{r},Transactions!$M$2:$M$2000),SUMIFS(Transactions!$M$2:$M$2000,Transactions!$C$2:$C$2000,A{r},Transactions!$E$2:$E$2000,Dashboard!$L$4)))',
            f'=IFERROR(H{r}/Dashboard!$A$8,0)'
        ])
    sh.get_range('H2:J46').formulas=cust_forms
    header(sh,'A1:J1');sh.freeze_panes.freeze_rows(1);setwidth(sh,'A:A',14);setwidth(sh,'B:B',28);setwidth(sh,'C:G',18);setwidth(sh,'H:I',24);setwidth(sh,'J:J',18)
    sh.get_range('H2:I46').set_number_format(YEN);sh.get_range('J2:J46').set_number_format(PCT)
    # Budget
    sh=ss['Budget'];heads=['月','四半期','部門ID','売上予算（円）','予定変動費率','予定変動費（円）','部門固定費予算（円）','共通費配賦予算（円）','利益予算（円）']
    rows=[];form=[]
    for idx,x in enumerate(BUDGET,2):
        rows.append([x['month'],x['quarter'],x['dept'],x['rev'],x['rate'],None,x['deptcost'],x['hqcost'],None])
        form.append((idx,f'=ROUND(D{idx}*E{idx},0)',f'=D{idx}-F{idx}-G{idx}-H{idx}'))
    sh.get_range('A1:I37').values=[heads]+rows
    sh.get_range('F2:F37').formulas=[[a] for r,a,b in form];sh.get_range('I2:I37').formulas=[[b] for r,a,b in form]
    header(sh,'A1:I1');setwidth(sh,'A:C',16);setwidth(sh,'D:I',22);sh.freeze_panes.freeze_rows(1)
    sh.get_range('D2:I37').set_number_format(YEN);sh.get_range('E2:E37').set_number_format(PCT)
    sh.get_range('D2:E37').format.font.color=INPUT;sh.get_range('G2:H37').format.font.color=INPUT
    # Monthly costs
    sh=ss['MonthlyCosts'];heads=['月','四半期','部門ID','人件費（円）','その他固定費（円）','固定費合計（円）']
    sh.get_range('A1:F49').values=[heads]+[[x['month'],x['quarter'],x['dept'],x['payroll'],x['overhead'],None] for x in COSTS]
    sh.get_range('F2:F49').formulas=[[f'=SUM(D{r}:E{r})'] for r in range(2,50)]
    header(sh,'A1:F1');setwidth(sh,'A:C',15);setwidth(sh,'D:F',22);sh.freeze_panes.freeze_rows(1)
    sh.get_range('D2:F49').set_number_format(YEN);sh.get_range('D2:E49').format.font.color=INPUT
    # Analysis
    sh=ss['Analysis'];heads=['月','部門ID','四半期','売上実績（円）','変動費（円）','限界利益（円）','部門固定費（円）','本社共通費配賦（円）','営業利益（円）','売上予算（円）','利益予算（円）','売上予算達成率','営業利益率']
    sh.get_range('A4:M40').values=[heads]+[[m,d,f'Q{(m-1)//3+1}']+[None]*10 for m in range(1,13) for d in ['IT','BPO','TRN']]
    forms=[]
    for r in range(5,41):
        m=f'$A{r}'; d=f'$B{r}'
        hq=f'SUMIFS(MonthlyCosts!$F$2:$F$49,MonthlyCosts!$A$2:$A$49,{m},MonthlyCosts!$C$2:$C$49,"HQ")'
        rate=f'INDEX(Divisions!$D$2:$D$4,MATCH({d},Divisions!$A$2:$A$4,0))'
        hqformula=f'=IF({d}="TRN",{hq}-ROUND({hq}*Divisions!$D$2,0)-ROUND({hq}*Divisions!$D$3,0),ROUND({hq}*{rate},0))'
        forms.append([
            f'=SUMIFS(Transactions!$H$2:$H$2000,Transactions!$B$2:$B$2000,{m},Transactions!$D$2:$D$2000,{d})',
            f'=SUMIFS(Transactions!$L$2:$L$2000,Transactions!$B$2:$B$2000,{m},Transactions!$D$2:$D$2000,{d})',
            f'=D{r}-E{r}',
            f'=SUMIFS(MonthlyCosts!$F$2:$F$49,MonthlyCosts!$A$2:$A$49,{m},MonthlyCosts!$C$2:$C$49,{d})',
            hqformula,
            f'=F{r}-G{r}-H{r}',
            f'=SUMIFS(Budget!$D$2:$D$37,Budget!$A$2:$A$37,{m},Budget!$C$2:$C$37,{d})',
            f'=SUMIFS(Budget!$I$2:$I$37,Budget!$A$2:$A$37,{m},Budget!$C$2:$C$37,{d})',
            f'=IFERROR(D{r}/J{r},0)', f'=IFERROR(I{r}/D{r},0)'
        ])
    sh.get_range('D5:M40').formulas=forms
    sh.merge_cells('A1:M2');sh.get_range('A1').values=[['MONTHLY PERFORMANCE | 部門別計算シート']]
    sh.get_range('A1:M2').format={'fill':NAVY,'font':{'bold':True,'color':WHITE,'size':14},'row_height':25}
    header(sh,'A4:M4');setwidth(sh,'A:C',14);setwidth(sh,'D:K',23);setwidth(sh,'L:M',18)
    sh.get_range('D5:K40').set_number_format(YEN);sh.get_range('L5:M40').set_number_format(PCT)
    sh.freeze_panes.freeze_rows(4)
    # Dashboard
    sh=ss['Dashboard'];sh.get_range('A1:P78').format.column_width=12.5
    sh.merge_cells('A1:P2');sh.get_range('A1').values=[['NBS-50   |   EXECUTIVE DASHBOARD']]
    sh.get_range('A1:P2').format={'fill':NAVY,'font':{'color':WHITE,'bold':True,'size':21},'row_height':25,'vertical_alignment':'center'}
    sh.merge_cells('A3:P3');sh.get_range('A3').values=[['FY2025  |  完全架空のBtoBサービス企業  |  従業員50名 / 3事業部  |  単位：百万円（KPIは円）']]
    sh.get_range('A3:P3').format={'fill':BLUE,'font':{'color':WHITE,'size':10},'row_height':23}
    sh.get_range('A4').values=[['事業部']];sh.merge_cells('B4:D4');sh.get_range('B4').values=[['全部門']]
    sh.get_range('K4').values=[['対象期間']];sh.merge_cells('L4:N4');sh.get_range('L4').values=[['通期']]
    for a in ['B4:D4','L4:N4']:
        sh.get_range(a).format={'fill':'#FFF1C7','font':{'color':INPUT,'bold':True,'size':12},'row_height':29,'vertical_alignment':'center'}
    sh.get_range('B4').data_validation={'rule':{'type':'list','values':['全部門','IT','BPO','TRN']}}
    sh.get_range('L4').data_validation={'rule':{'type':'list','values':['通期','Q1','Q2','Q3','Q4']}}
    kpis=[('A6:D6','A8:D9','売上高','A8'),('E6:H6','E8:H9','営業利益','E8'),('I6:L6','I8:L9','営業利益率','I8'),('M6:P6','M8:P9','売上予算達成率','M8')]
    for top,val,label,addr in kpis:
        sh.merge_cells(top);sh.get_range(top.split(':')[0]).values=[[label]]
        sh.get_range(top).format={'fill':PALE,'font':{'color':BLUE,'bold':True,'size':11},'row_height':27}
        sh.merge_cells(val);sh.get_range(val).format={'fill':LT,'font':{'color':NAVY,'bold':True,'size':25},'row_height':25,'vertical_alignment':'center'}
    def filter_sum(col):
        full=f'Analysis!${col}$5:${col}$40'
        return (f'=IF($B$4="全部門",IF($L$4="通期",SUM({full}),SUMIF(Analysis!$C$5:$C$40,$L$4,{full})),'
                f'IF($L$4="通期",SUMIF(Analysis!$B$5:$B$40,$B$4,{full}),'
                f'SUMIFS({full},Analysis!$B$5:$B$40,$B$4,Analysis!$C$5:$C$40,$L$4)))')
    sh.get_range('A8').formulas=[[filter_sum('D')]];sh.get_range('E8').formulas=[[filter_sum('I')]]
    sh.get_range('I8').formulas=[['=IFERROR(E8/A8,0)']];sh.get_range('M8').formulas=[[f'=IFERROR(A8/({filter_sum("J")[1:]}),0)']]
    sh.get_range('A8').set_number_format(YEN);sh.get_range('E8').set_number_format(YEN)
    sh.get_range('I8').set_number_format(PCT);sh.get_range('M8').set_number_format(PCT)
    sh.merge_cells('A11:P11');sh.get_range('A11').values=[['DECISION SIGNALS     /     経営リスクの確認']]
    sh.get_range('A11:P11').format={'fill':NAVY,'font':{'color':WHITE,'bold':True},'row_height':24}
    sh.merge_cells('A12:F12');sh.get_range('A12').values=[['売上上位5顧客構成比']]
    sh.merge_cells('G12:J12');sh.get_range('G12').formulas=[['=IFERROR(SUM($D$60:$D$64)*1000000/$A$8,0)']];sh.get_range('G12').set_number_format(PCT)
    sh.merge_cells('K12:P12');sh.get_range('K12').values=[['契約集中リスク（数値で判定）']]
    sh.merge_cells('A13:J13');sh.get_range('A13').values=[['予算差異（売上高）']]
    sh.merge_cells('K13:P13');sh.get_range('K13').formulas=[[f'=A8-({filter_sum("J")[1:]})']];sh.get_range('K13').set_number_format(YEN)
    sh.merge_cells('A14:P14');sh.get_range('A14').values=[['※事業部／対象期間は上部セルで変更可能。顧客ランキングも選択条件に連動します。']]
    sh.get_range('A14:P14').format={'font':{'color':MUTED,'size':9},'row_height':20}
    sh.merge_cells('A18:J18');sh.get_range('A18').values=[['MONTHLY TREND  /  売上実績と予算（百万円）']]
    sh.merge_cells('K18:P18');sh.get_range('K18').values=[['DIVISION PERFORMANCE  /  営業利益（百万円）']]
    sh.get_range('A18:P18').format={'fill':PALE,'font':{'color':NAVY,'bold':True},'row_height':24}
    sh.merge_cells('A39:P39');sh.get_range('A39').values=[['SUPPORTING TABLES  /  グラフの集計元データ（自動更新）']]
    sh.get_range('A39:P39').format={'fill':NAVY,'font':{'color':WHITE,'bold':True},'row_height':24}
    # monthly graph table
    sh.get_range('A41:D41').values=[['月','実績（百万円）','予算（百万円）','営業利益（百万円）']]
    monthforms=[]
    for m in range(1,13):
        r=41+m
        def month_sum(col):
            return f'=IF($B$4="全部門",SUMIF(Analysis!$A$5:$A$40,{m},Analysis!${col}$5:${col}$40),SUMIFS(Analysis!${col}$5:${col}$40,Analysis!$A$5:$A$40,{m},Analysis!$B$5:$B$40,$B$4))/1000000'
        monthforms.append([f'{m}月',None,None,None])
    sh.get_range('A42:D53').values=monthforms
    sh.get_range('B42:D53').formulas=[[month_sum.replace('__r__',str(r)) for month_sum in [
        f'=IF($B$4="全部門",SUMIF(Analysis!$A$5:$A$40,{m},Analysis!$D$5:$D$40),SUMIFS(Analysis!$D$5:$D$40,Analysis!$A$5:$A$40,{m},Analysis!$B$5:$B$40,$B$4))/1000000',
        f'=IF($B$4="全部門",SUMIF(Analysis!$A$5:$A$40,{m},Analysis!$J$5:$J$40),SUMIFS(Analysis!$J$5:$J$40,Analysis!$A$5:$A$40,{m},Analysis!$B$5:$B$40,$B$4))/1000000',
        f'=IF($B$4="全部門",SUMIF(Analysis!$A$5:$A$40,{m},Analysis!$I$5:$I$40),SUMIFS(Analysis!$I$5:$I$40,Analysis!$A$5:$A$40,{m},Analysis!$B$5:$B$40,$B$4))/1000000'
    ]] for r,m in [(42+i,1+i) for i in range(12)]]
    header(sh,'A41:D41');sh.get_range('B42:D53').set_number_format(MM)
    sh.get_range('K41:O41').values=[['事業部','売上（百万円）','利益（百万円）','利益率','予算達成率']]
    sh.get_range('K42:K44').values=[['IT'],['BPO'],['TRN']]
    dept_forms=[]
    for r in range(42,45):
        def period_sum(col):
            return f'IF($L$4="通期",SUMIF(Analysis!$B$5:$B$40,K{r},Analysis!${col}$5:${col}$40),SUMIFS(Analysis!${col}$5:${col}$40,Analysis!$B$5:$B$40,K{r},Analysis!$C$5:$C$40,$L$4))'
        dept_forms.append([f'={period_sum("D")}/1000000', f'={period_sum("I")}/1000000', f'=IFERROR(M{r}/L{r},0)', f'=IFERROR(L{r}*1000000/{period_sum("J")},0)'])
    sh.get_range('L42:O44').formulas=dept_forms
    header(sh,'K41:O41');sh.get_range('L42:M44').set_number_format(MM);sh.get_range('N42:O44').set_number_format(PCT)
    sh.merge_cells('A57:F57');sh.get_range('A57').values=[['CUSTOMER RANKING  /  選択条件内の売上上位5社']]
    sh.get_range('A57:F57').format={'fill':NAVY,'font':{'color':WHITE,'bold':True},'row_height':25}
    sh.get_range('A59:D59').values=[['順位','顧客ID','顧客名','売上（百万円）']];header(sh,'A59:D59')
    for rank in range(1,6):
        r=59+rank;sh.get_range(f'A{r}').values=[[rank]]
        sh.get_range(f'D{r}').formulas=[[f'=LARGE(Customers!$H$2:$H$46,A{r})/1000000']]
        sh.get_range(f'B{r}').formulas=[[f'=INDEX(Customers!$A$2:$A$46,MATCH(D{r}*1000000,Customers!$H$2:$H$46,0))']]
        sh.get_range(f'C{r}').formulas=[[f'=INDEX(Customers!$B$2:$B$46,MATCH(B{r},Customers!$A$2:$A$46,0))']]
    sh.get_range('D60:D64').set_number_format(MM)
    sh.merge_cells('A67:P67');sh.get_range('A67').values=[['DATA REFRESH / 更新ルール']]
    sh.get_range('A67:P67').format={'fill':NAVY,'font':{'color':WHITE,'bold':True},'row_height':25}
    for row,desc in enumerate([
        '1. Transactionsに新規行を追加。顧客ID・部門IDを既存マスタに合わせ、売上・外注費・ライセンス費・その他変動費を入力。',
        '2. 変動費計（L列）と限界利益（M列）の数式を新規行にコピー。集計範囲は2～2000行まで対応。',
        '3. BudgetとMonthlyCostsの数値は必要に応じて変更。Dashboard上部で対象部門・期間を選択。',
        '4. Validationの差異ゼロ／エラー件数ゼロを確認。AI生成の架空企業データであり、実在の企業情報は含まない。'
    ],69):
        sh.merge_cells(f'A{row}:P{row}');sh.get_range(f'A{row}').values=[[desc]]
        sh.get_range(f'A{row}:P{row}').format={'font':{'color':MUTED,'size':9},'row_height':23}
    sh.get_range('A4:P4').format.row_height=30
    # Charts, bound to live Excel formulas
    try:
        line=sh.charts.add('line',{'title':'月次売上実績と予算（百万円）','has_legend':True})
        for label,col in [('実績','B'),('予算','C')]:
            ser=line.series.add(label)
            ser.category_formula="'Dashboard'!$A$42:$A$53"
            ser.formula=f"'Dashboard'!${col}$42:${col}$53"
        line.legend.position='bottom';line.set_position('A19','J37')
    except Exception as e: print('CHART1_WARNING',str(e)[:250])
    try:
        bars=sh.charts.add('bar',{'title':'部門別営業利益（百万円）','has_legend':False})
        bars.bar_options.direction='column';bars.bar_options.grouping='clustered'
        ser=bars.series.add('営業利益');ser.category_formula="'Dashboard'!$K$42:$K$44";ser.formula="'Dashboard'!$M$42:$M$44"
        bars.set_position('K19','P37')
    except Exception as e: print('CHART2_WARNING',str(e)[:250])
    # Validation
    sh=ss['Validation'];title(sh,'CONTROL & RECONCILIATION | 数値整合性チェック','F')
    sh.get_range('A4:D4').values=[['検証項目','照合元（円・件）','照合先（円・件）','差異（ゼロなら合格）']]
    header(sh,'A4:D4');setwidth(sh,'A:A',42);setwidth(sh,'B:D',26)
    checks=[
      ('売上:取引明細 vs 月次分析','=SUM(Transactions!H2:H2000)','=SUM(Analysis!D5:D40)'),
      ('変動費:取引明細 vs 月次分析','=SUM(Transactions!L2:L2000)','=SUM(Analysis!E5:E40)'),
      ('限界利益:売上-変動費','=SUM(Analysis!D5:D40)-SUM(Analysis!E5:E40)','=SUM(Analysis!F5:F40)'),
      ('部門固定費:費用表 vs 分析','=SUMIF(MonthlyCosts!C2:C49,"<>HQ",MonthlyCosts!F2:F49)','=SUM(Analysis!G5:G40)'),
      ('本社共通費:費用表 vs 配賦','=SUMIF(MonthlyCosts!C2:C49,"HQ",MonthlyCosts!F2:F49)','=SUM(Analysis!H5:H40)'),
      ('営業利益:売上-総費用','=SUM(Transactions!H2:H2000)-SUM(Transactions!L2:L2000)-SUM(MonthlyCosts!F2:F49)','=SUM(Analysis!I5:I40)'),
      ('売上予算:予算表 vs 分析','=SUM(Budget!D2:D37)','=SUM(Analysis!J5:J40)'),
      ('営業利益予算:予算表 vs 分析','=SUM(Budget!I2:I37)','=SUM(Analysis!K5:K40)'),
      ('社員数:人員構成 vs 50','=SUM(Divisions!C2:C5)','=50'),
      ('取引明細:残余行数（最大2000行）','=COUNTA(Transactions!A2:A2000)','=COUNTA(Transactions!H2:H2000)')
    ]
    sh.get_range('A5:D14').values=[[t,None,None,None] for t,b,c in checks]
    sh.get_range('B5:D14').formulas=[[b,c,f'=B{r}-C{r}'] for r,(_,b,c) in enumerate(checks,5)]
    sh.get_range('B5:D14').set_number_format(YEN)
    sh.get_range('A17').values=[['検証ステータス']];sh.get_range('B17').formulas=[['=IF(SUM(ABS(D5),ABS(D6),ABS(D7),ABS(D8),ABS(D9),ABS(D10),ABS(D11),ABS(D12),ABS(D13),ABS(D14))=0,"PASS","REVIEW")']]
    sh.get_range('B17').format={'fill':PALE,'font':{'bold':True,'color':GREEN,'size':13},'row_height':27}
    sh.get_range('A19').values=[['備考']];sh.merge_cells('B19:F19');sh.get_range('B19').values=[['ID重複・未知ID・変動費不一致は独立Python検算でも検証済。新規行の数式コピーを確認してください。']]
    sh.get_range('B19:F19').format={'font':{'color':MUTED,'size':9}}
    sh.get_range('D5:D14').conditional_formats.add_cell_is({'operator':'notEqual','formula':0,'format':{'fill':'#FCE4E4','font':{'color':RED}}})
    # guide
    sh=ss['Guide_AI_Log'];title(sh,'PROJECT NOTES & AI TRACE | ポートフォリオ制作記録','H')
    setwidth(sh,'A:A',24);setwidth(sh,'B:B',88);setwidth(sh,'C:H',18)
    guide=[
        ('モデル設定','2025年度 / 50名（事業45名・HQ5名） / 3事業部 / 45顧客 / 608取引。すべて完全架空。'),
        ('会計上の定義','営業利益 = 取引売上高 - 外注・ライセンス等変動費 - 事業部人件費等固定費 - 本社固定費。税・金利は対象外。'),
        ('原価二重計上防止','Transactionsの変動費に社員給与を含めない。社員給与はMonthlyCostsに一度だけ計上。'),
        ('本社共通費配賦','月次の本社固定費を45名の事業部員数比で配賦（IT20 / BPO15 / TRN10）。端数1円はTRN部門に調整。'),
        ('分析期間','期間選択は通期、Q1、Q2、Q3、Q4。部門選択は全部門、IT、BPO、TRN。'),
        ('更新上限','Transactionsの集計数式は2～2000行。追加取引のL列・M列数式をコピーすること。'),
        ('仮定の独立性','売上予算・固定費予算は事業計画値として別途設定。売上実績の単純な割合ではない。'),
        ('AI実装 1','架空企業・取引シナリオ・原価ルール・予算設計をAI支援で設計。人間は前提と現実性を要確認。'),
        ('AI実装 2','Pythonによる乱数固定（seed 20261011）のデータ生成、整合性検証、Excel数式生成。'),
        ('AI実装 3','PDFレポート文案・分析構成・改善提案をAI支援で作成。因果関係と施策実行可能性は人間が要検討。'),
        ('修正履歴 1','費用配賦の円単位端数不一致を検出 → TRN部門へ差額調整し、配賦合計を完全一致させた。'),
        ('修正履歴 2','初回の売上予算が実績比で過大だったため、実績を変えずに架空事前計画の予算前提を調整した。'),
        ('確認対象','架空であることの表示、データの更新動作、Excelでの再計算、商用利用前の実データ移行・個人情報管理。'),
        ('成果物','Excelダッシュボード / 3ページ経営レポート（PDF） / 制作・検算ログ（TXT）')
    ]
    sh.get_range('A4:B17').values=[[a,b] for a,b in guide]
    sh.get_range('A4:A17').format={'fill':PALE,'font':{'bold':True,'color':BLUE},'row_height':32}
    sh.get_range('B4:B17').format={'font':{'color':INK,'size':10},'row_height':32,'wrap_text':True}
    # set tables after formulas and raw data; limits to actual data, allowing normal Excel Table extension.
    for name,addr,table_name in [('Transactions',f'A1:M{len(TX)+1}','tblTransactions'),('Customers','A1:J46','tblCustomers'),('Budget','A1:I37','tblBudget'),('MonthlyCosts','A1:F49','tblCosts')]:
        try:ss[name].tables.add(addr,True,table_name)
        except Exception as e: print('TABLE_WARNING',name,str(e)[:250])
    path=str(BASE/'01_経営分析ダッシュボード.xlsx')
    try:
        print('DASHBOARD_INSPECT',wb.inspect({'kind':'table','range':'Dashboard!A6:P13','include':'values,formulas','table_max_rows':10,'table_max_cols':16}).ndjson[:3200])
        print('ANALYSIS_INSPECT',wb.inspect({'kind':'table','range':'Analysis!A4:M8','include':'values,formulas','table_max_rows':5,'table_max_cols':13}).ndjson[:2400])
    except Exception as e:print('INSPECT_WARNING',str(e)[:400])
    SpreadsheetFile.export_xlsx(wb).save(path)
    print('XLSX_CREATED',path,os.path.getsize(path))
    try:
        wb.render({'sheet_name':'Dashboard','range':'A1:P17','scale':1.2}).save(str(BASE/'_dashboard_preview.png'))
        print('DASHBOARD_RENDERED')
    except Exception as e:print('RENDER_WARNING',str(e)[:300])
    try:
        err=wb.inspect({'kind':'match','search_term':'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A','options':{'use_regex':True,'max_results':15}})
        print('ERROR_SCAN',err.ndjson[:1200])
    except Exception as e:print('ERROR_SCAN_WARNING',str(e)[:300])
    return path

def make_pdf():
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.lib.colors import HexColor, Color, white
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
    FONT='HeiseiKakuGo-W5'
    file=str(BASE/'01_経営改善提案レポート.pdf')
    can=canvas.Canvas(file,pagesize=A4,pageCompression=1)
    W,H=A4; LM=43; RM=43; DW=W-LM-RM
    N=HexColor(NAVY); BL=HexColor(BLUE); T=HexColor(TEAL); BG=HexColor(LT); MD=HexColor(MUTED); REDC=HexColor(RED)
    by=SUMMARY['bydept']; revenue=SUMMARY['revenue']; profit=SUMMARY['profit']; att=SUMMARY['achievement']; margin=SUMMARY['margin']
    q3trn=sum(a['profit'] for a in SUMMARY['analysis'] if a['quarter']=='Q3' and a['dept']=='TRN')
    q4bpo=sum(a['profit'] for a in SUMMARY['analysis'] if a['quarter']=='Q4' and a['dept']=='BPO')
    q4bpo_rev=sum(a['revenue'] for a in SUMMARY['analysis'] if a['quarter']=='Q4' and a['dept']=='BPO')
    trn_q3_rev=sum(a['revenue'] for a in SUMMARY['analysis'] if a['quarter']=='Q3' and a['dept']=='TRN')
    IT_REV=by['IT']['revenue']
    fmt=lambda v:f'{v/1e6:,.1f}'
    def txt(x,y,t,size=10,color=N):
        can.setFillColor(color);can.setFont(FONT,size);can.drawString(x,y,str(t))
    def text_right(x,y,t,size=10,color=N):
        can.setFillColor(color);can.setFont(FONT,size);can.drawRightString(x,y,str(t))
    def split_lines(t,max_width,font_size):
        lines=[];buf=''
        for char in t:
            if char=='\n':
                lines.append(buf);buf='';continue
            test=buf+char
            if pdfmetrics.stringWidth(test,FONT,font_size)>max_width and buf:
                lines.append(buf);buf=char
            else:buf=test
        if buf:lines.append(buf)
        return lines
    def paragraph(x,y,t,width,fs=10,leading=16,color=N,maxlines=10):
        lines=split_lines(t,width,fs)
        if len(lines)>maxlines:raise ValueError(f'PDF text will overflow: {t[:35]}')
        for ln in lines:
            txt(x,y,ln,fs,color);y-=leading
        return y
    def box(x,y,w,h,fill=BG,r=9):
        can.setFillColor(fill);can.roundRect(x,y-h,w,h,r,fill=1,stroke=0)
    def rule(y):can.setStrokeColor(HexColor('#DDE7ED'));can.line(LM,y,W-RM,y)
    def page(eyebrow,title,subtitle,page_num):
        can.setFillColor(N);can.rect(0,H-125,W,125,fill=1,stroke=0)
        txt(LM,H-43,eyebrow,10,HexColor('#7DDFE1'))
        txt(LM,H-76,title,21,white)
        txt(LM,H-100,subtitle,9,HexColor('#D1E6EF'))
        rule(41)
        txt(LM,25,'PORTFOLIO 01  /  NBS-50（完全架空企業）  /  FY2025',8,MD)
        text_right(W-RM,25,f'{page_num} / 3',8,MD)
    def subhead(y,s):
        txt(LM,y,s,13,BL);can.setFillColor(T);can.roundRect(LM,y-12,31,3,1.5,fill=1,stroke=0)
    # Page 1
    page('EXECUTIVE BRIEF  |  2025年度', '経営分析・改善提案', '売上の未達と利益構造を可視化し、意思決定の優先順位を整理',1)
    y=H-155
    kpis=[('売上高',f'¥{fmt(revenue)}M'),('営業利益',f'¥{fmt(profit)}M'),('営業利益率',f'{margin*100:.1f}%'),('売上予算達成率',f'{att*100:.1f}%')]
    g=9;cw=(DW-3*g)/4
    for i,(label,value) in enumerate(kpis):
        x=LM+i*(cw+g);box(x,y,cw,78)
        txt(x+11,y-23,label,8,MD);txt(x+11,y-53,value,16,T if i==1 else N)
    y-=103
    subhead(y,'経営サマリー');y-=26
    y=paragraph(LM,y,f'年間売上高は{fmt(revenue)}百万円、予算{fmt(SUMMARY["budget"])}百万円に対し達成率{att*100:.1f}%。売上予算差は{fmt(revenue-SUMMARY["budget"])}百万円。営業利益は{fmt(profit)}百万円、利益率は{margin*100:.1f}%。',DW,9.5,16)
    y-=16
    subhead(y,'月次売上：実績と予算（百万円）');y-=24
    cx=LM+34; chart_y_top=y;plot_h=125;plot_w=DW-50;plot_y_bottom=chart_y_top-plot_h
    monthly=[]
    for m in range(1,13):
        ach=sum(a['revenue'] for a in SUMMARY['analysis'] if a['month']==m)/1e6
        bud=sum(a['budget'] for a in SUMMARY['analysis'] if a['month']==m)/1e6
        monthly.append((m,ach,bud))
    mx=math.ceil(max(max(x[1],x[2]) for x in monthly)/10)*10
    for tick in range(0,mx+1,20):
        yp=plot_y_bottom+plot_h*tick/mx;can.setStrokeColor(HexColor('#E4ECF1'));can.line(cx,yp,cx+plot_w,yp)
        text_right(cx-8,yp-3,str(tick),7,MD)
    for idx,col in enumerate([1,2]):
        pts=[(cx+i*(plot_w/11),plot_y_bottom+plot_h*row[col]/mx) for i,row in enumerate(monthly)]
        can.setLineWidth(2.3 if idx==0 else 1.5);can.setStrokeColor(T if idx==0 else HexColor('#93A5B7'))
        if idx==1:can.setDash(4,3)
        p=can.beginPath();p.moveTo(*pts[0]);[p.lineTo(*xy) for xy in pts[1:]];can.drawPath(p)
        can.setDash()
    for i in range(12):
        if i%2==0:txt(cx+i*(plot_w/11)-5,plot_y_bottom-16,str(i+1),7,MD)
    txt(cx+4,plot_y_bottom-32,'●  売上実績',8,T);txt(cx+111,plot_y_bottom-32,'---  売上予算',8,MD)
    y=plot_y_bottom-63
    subhead(y,'部門別損益');y-=26
    cols=[LM,LM+148,LM+254,LM+372,DW+LM];rowh=25
    box(LM,y+14,DW,29,fill=N,r=4)
    for x,a in zip(cols[:-1],['部門','売上（百万円）','利益（百万円）','営業利益率']):txt(x+8,y+3,a,8,white)
    y-=24
    for j,(d,n,h) in enumerate(DEPTS[:3]):
        p=by[d]['profit'];v=by[d]['revenue']
        if j%2==0:box(LM,y+11,DW,rowh,fill=BG,r=0)
        txt(LM+8,y,d+' | '+n[:7],8.5)
        text_right(cols[2]-16,y,fmt(v),9)
        text_right(cols[3]-14,y,fmt(p),9,REDC if p<1e6 else N)
        text_right(cols[4]-11,y,f'{p/v*100:.1f}%',9)
        y-=rowh
    y-=15
    box(LM,y+8,DW,61,fill=HexColor('#E5F2F1'))
    txt(LM+12,y-11,'経営判断の優先順位',10,T)
    paragraph(LM+12,y-28,'① IT部門の採算改善  ② BPO部門の第4四半期原価改善  ③ 研修部門の第3四半期需要平準化',DW-24,9,15)
    can.showPage()
    # Page 2
    page('DIAGNOSIS  |  課題の抽出', '重要経営課題 3件', '根拠と原因仮説を区別して検討。仮説は追加調査が必要',2)
    y=H-154
    problems=[
     ('01','IT導入支援：売上規模が大きいのに利益が残らない',
      f'売上 {fmt(by["IT"]["revenue"])}百万円／営業利益 {fmt(by["IT"]["profit"])}百万円／利益率 {by["IT"]["profit"]/by["IT"]["revenue"]*100:.1f}%。売上予算差 {fmt(by["IT"]["revenue"]-by["IT"]["budget"])}百万円。',
      '仮説：案件の値付けが固定費を十分に回収できない。契約種別別の採算と稼働率を確認する。',
      '提案：案件別の限界利益・工数を比較し、低採算契約の価格改定／提供工程標準化を検討。'),
     ('02','BPO：第4四半期に収益性が悪化',
      f'第1四半期利益 {fmt(sum(a["profit"] for a in SUMMARY["analysis"] if a["dept"]=="BPO" and a["quarter"]=="Q1"))}百万円から第4四半期 {fmt(q4bpo)}百万円へ。第4四半期は赤字。',
      '仮説：外注単価や変動費率の上昇、追加対応による人件費負担の増加。契約・発注単価を確認する。',
      '提案：外注先の再見積もり、例外業務の追加請求、品質を維持した標準化を実行。'),
     ('03','企業研修：第3四半期に赤字が集中',
      f'第3四半期売上 {fmt(trn_q3_rev)}百万円／営業利益 {fmt(q3trn)}百万円。年間利益は {fmt(by["TRN"]["profit"])}百万円でほぼ損益均衡。',
      '仮説：夏場の受注減少を固定的な人員・設備費が吸収できない。実施時期・成約率を確認する。',
      '提案：閑散期向け短時間コースの新設、継続契約の前倒し販売、講師稼働の調整。')
    ]
    for no,h1,evidence,hypo,proposal in problems:
        box(LM,y,DW,180,fill=BG)
        txt(LM+14,y-27,no,17,T)
        txt(LM+54,y-27,h1,11,BL)
        yy=y-54
        yy=paragraph(LM+16,yy,'観測事実：'+evidence,DW-34,9.2,15)
        yy-=9
        yy=paragraph(LM+16,yy,hypo,DW-34,9.1,15)
        yy-=8
        yy=paragraph(LM+16,yy,proposal,DW-34,9.1,15)
        y-=193
    txt(LM,y-8,'監視指標：売上上位5顧客比率 27.9%（集中度の参考指標。単独で危機水準とは判定しない）',9,MD)
    can.showPage()
    # Page 3
    page('ACTION PLAN  |  施策と検証', '改善ロードマップ', '仮説を小規模に試し、利益改善を実測する',3)
    y=H-154
    subhead(y,'90日アクション');y-=27
    steps=[('0〜30日','実態把握','契約別・取引別収益と稼働時間を点検。BPO外注単価、研修失注理由を洗い出す。'),
           ('31〜60日','施策試行','ITの価格改定対象を抽出。BPO発注・作業標準化を試行。研修の閑散期商品を試験販売。'),
           ('61〜90日','効果検証','利益率・予算達成率・稼働率を再測定し、継続・変更・中止を判断。')]
    for i,(period,title1,body) in enumerate(steps):
        box(LM,y+12,DW,57,fill=BG)
        txt(LM+12,y-4,period,11,T);txt(LM+105,y-4,title1,10,BL)
        paragraph(LM+105,y-23,body,DW-118,9,14)
        y-=61
    y-=10;subhead(y,'施策の感度分析（実績からの試算、確約値ではない）');y-=27
    savings=[('ITの平均実現単価 +2%',IT_REV*.02,'価格上昇分が100%利益に寄与する仮定'),
            ('BPOのQ4変動費率 -5pt',q4bpo_rev*.05,'Q4売上一定・品質維持の仮定'),
            ('研修Q3に10講座追加',10*800000*.80,'1講座80万円、限界利益率80%の仮定')]
    box(LM,y+14,DW,29,fill=N,r=3)
    txt(LM+9,y+3,'試算条件',9,white);text_right(W-RM-12,y+3,'営業利益への増分',9,white)
    y-=26
    for title1,imp,assumption in savings:
        txt(LM+9,y,title1,9,BL);text_right(W-RM-12,y,f'+{fmt(imp)}百万円',10,T)
        y-=17
        txt(LM+9,y,'前提：'+assumption,8,MD)
        y-=22
    y-=12
    box(LM,y+12,DW,60,fill=HexColor('#E6F1F0'))
    txt(LM+13,y-8,'改善余地の単純合計（相互影響未考慮）',9,T)
    txt(LM+13,y-34,f'+{fmt(sum(x[1] for x in savings))}百万円   →   試算後営業利益 {fmt(profit+sum(x[1] for x in savings))}百万円',13,N)
    y-=87
    subhead(y,'KPIと管理ルール');y-=22
    for line in [
      'IT：案件別限界利益・稼働時間・単価改定実現率を月次で確認。',
      'BPO：月次変動費率、契約外工数、外注単価を月次で確認。',
      '研修：受注件数、講座開催数、講師稼働率を月次で確認。'
    ]:y=paragraph(LM,y,'・'+line,DW,9,15)-4
    y-=16;rule(y);y-=18
    y=paragraph(LM,y,'データ・免責：本資料は2025年の完全架空取引608件、顧客45社をAI支援で生成した分析演習。因果関係は仮説であり、改善効果は条件付き試算。実在企業の実績や専門家による監査結果ではない。数値は独立したPython集計とExcel集計で照合。',DW,8.3,13,MD)
    can.showPage();can.save()
    print('PDF_CREATED',file,os.path.getsize(file))
    return file

def make_log():
    a=SUMMARY; q3=sum(x['profit'] for x in a['analysis'] if x['dept']=='TRN' and x['quarter']=='Q3')
    q4=sum(x['profit'] for x in a['analysis'] if x['dept']=='BPO' and x['quarter']=='Q4')
    lines=[
        '# AI活用・制作・検算記録｜第1作 経営分析ダッシュボード',
        '制作日：2026-10-11',
        '目的：AI関連企業への転職ポートフォリオ。架空企業のデータ設計→集計→判断→提案の一連の実装。',
        '',
        '【制作物】',
        '01_経営分析ダッシュボード.xlsx：9シート、更新・選択可能な数式・チャート、元取引608件。',
        '01_経営改善提案レポート.pdf：経営分析、重要課題3件、90日施策、条件付き効果試算。',
        '01_AI活用_制作検算ログ.txt：本ファイル。',
        '',
        '【生成条件と財務定義】',
        '会社：NBS-50（完全架空）。従業員50名（IT20／BPO15／研修10／本社5）。',
        '対象：2025年1〜12月。完全架空の法人顧客45社、取引明細608行。',
        '社員給与はMonthlyCostsにのみ計上。取引明細の変動費は外注・ライセンス・その他外部費用のみ。',
        '営業利益＝売上高－変動費－全部門固定費－本社固定費。',
        '本社固定費は事業部在籍人数 20:15:10 で配賦し、円未満端数をTRNで調整。',
        '乱数seed=20261011。全数値は人工的な仮定で、実在企業情報・外部サイト・個人情報を使用しない。',
        '',
        '【検算ログ／独立Python集計】',
        f'取引数 = {a["n_tx"]}件、顧客 = {a["n_customers"]}社。',
        f'売上 = {a["revenue"]:,}円。変動費 = {a["variable"]:,}円。営業利益 = {a["profit"]:,}円。',
        f'予算 = {a["budget"]:,}円。売上予算達成率 = {a["achievement"]:.10%}。営業利益率 = {a["margin"]:.10%}。',
        '売上・変動費・限界利益・部門固定費・HQ配賦・営業利益・売上予算：Python assert によりすべて一致。',
        '取引ID重複なし、顧客ID欠損なし、顧客所属部門と取引所属部門の不一致なし、売上＜変動費の取引なし。',
        'Excel Validationシートの全10項目：差異ゼロを合格基準として設定。',
        'Excel 更新仕様：Transactionsの2〜2000行を集計。追加行の計算式をコピーしValidationを確認。',
        '',
        '【主要課題（生成データから計算）】',
        f'課題1 IT低採算：利益 {a["bydept"]["IT"]["profit"]:,}円、利益率 {a["bydept"]["IT"]["profit"]/a["bydept"]["IT"]["revenue"]:.2%}。',
        f'課題2 BPO Q4赤字：営業利益 {q4:,}円。',
        f'課題3 研修 Q3赤字：営業利益 {q3:,}円。',
        f'参考値 売上上位5社比率 {a["top5_share"]:.2%}。これだけで過度な集中とは断定しない。',
        '',
        '【AIに依頼した作業の要約（逐語プロンプトではなく指示要旨）】',
        '1. 従業員50名・3事業部・12か月・顧客別取引データを作成すること。',
        '2. 収益・費用を二重計上せず、本社費用を人員比で配賦すること。',
        '3. 予算・費用・顧客・取引のテーブルを分離し、部門と四半期で絞り込めるExcelを作ること。',
        '4. PythonとExcelで金額の一致を検算し、経営課題3件を分析すること。',
        '5. 日本語の経営者向け3ページPDFと90日改善アクションを作ること。',
        '',
        '【発見した問題と修正の記録】',
        '修正1：本社固定費の配賦端数により月次配賦合計が1円単位で一致しない問題を検出。',
        '      → IT/BPOを四捨五入し研修に残額を割当てる処理へ変更、差額0円を確認。',
        '修正2：初回売上予算が年間実績に対して大幅に過大だったため、架空事前予算の前提を再調整。',
        '      → 取引実績を改変せず予算側の設定を変更した。',
        '修正3：Excel Validationの配列ABS+SUMPRODUCTが一部計算エンジンで#VALUE!となった。',
        '      → SUM(ABS(D5),ABS(D6),...)の標準式へ変更。',
        '',
        '【AIの役割と人間が確認すべき点】',
        'AI：架空データ設計、Pythonデータ生成、Excel数式・可視化、検算ロジック、PDFの文章・デザイン。',
        '人間：想定企業の業務妥当性、原因仮説の調査、改善施策の実行コストと顧客影響、数値の最終承認。',
        '注意：数字は練習用架空シナリオ。実際のコンサル実績や人間による監査完了を意味しない。',
        '',
        '【次の確認】',
        'Excelで事業部/四半期の絞込、取引1行の売上変更、追加行、PDF文字の表示を確認する。',
    ]
    path=BASE/'01_AI活用_制作検算ログ.txt'
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('LOG_CREATED',path,os.path.getsize(path))
    return str(path)

if __name__=='__main__':
    make_workbook();make_pdf();make_log()
