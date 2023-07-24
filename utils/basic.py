import smtplib

def rename_dataframe(df, ):
    columns = {'买价' : 'buy' , 
                '卖价' : 'sell', 
                '行权价' : 'exercise', 
                '最新价' : 'close',
                '买价_short' : 'buy_short' , 
                '卖价_short' : 'sell_short', 
                '行权价_short' : 'exercise_short',
                '看涨合约-买价'  : 'buy',
                '看涨合约-最新价'  : 'close',
                '看涨合约-卖价'    : 'sell', 
                '行权价' : 'exercise', 
                'bprice'  : 'buy',
                'lastprice'  : 'close',
                'sprice'    : 'sell', 
                '开盘价'    : 'open', 
                '昨收价' : 'pre_close', 
                '收盘价'  : 'close',
                '最高价'  : 'high',
                '最低价'    : 'low', 
                '成交量':'volume', 
                '成交额': 'amount',
                '日期' : 'date',
                '开盘'    : 'open', 
                '昨收' : 'pre_close', 
                '收盘'  : 'close',
                '最高'  : 'high',
                '最低'    : 'low', 
                }
    return df.rename(columns = columns)

class Bar:

    def update_bar(self, df ):
        self.open = float(df.open)
        self.high = float(df.high)
        self.low = float(df.low)
        self.close = float(df.close)
        self.volume = float(df.volume)
        

        for i in ['date','open_interest','pre_close']:
            try:
                setattr(self, i, float(df[i]))
            except:
                pass


        return self

    def __repr__(self) -> str:
        return f'open : {self.open}, close : {str(self.close)}, return : {str((self.close/self.pre_close - 1)* 100) } %'
        
name_2_symbol = {   
                '沪深300':'sh510300', 
                '（深）沪深300' : 'sz159919', 
                '光伏':'sh515790',
                '中证500' : 'sh510500' ,
                '科创50' : 'sh588000',
                '新能源':'sh516160',
                '消费':'sz159928',
                '半导体' : 'sh512480',
                '上证50' : 'sh510050',
                '创业板综' : 'sz399102',
                '创业板指' : 'sz159915',
                '军工' : 'sh512660',
                '创新药':'sz159992',
                '创业板50':'sz159949',
                '人工智能':'sz159819',
                '央企创新驱动':'sh515900',
                '传媒' : 'sz159805',
                '家电' : 'sz159996',
                '新能源车' : 'sh515030',
                '煤炭' : 'sh515220',
                '大宗商品' : 'sh510170',
                '消费30' : 'sh510630',
                '有色金属' : 'sh512400',
                '沪深300index' : 'sh000300'

}

def send_email( FROM,
                TO, 
                CONTENT = 'None', 
                HOST = 'smtp.126.com', 
                SUBJECT = 'title', 
                attachs = None, 
                PORT = '25',
                password='VPZHHOBAXTYGREZU'):
    try:

        #设置服务器所需信息
        HOST = HOST
        # 2> 配置服务的端口，默认的邮件端口是25.
        PORT = PORT
        # 3> 指定发件人和收件人。
        FROM = FROM
        TO = TO
        # 4> 邮件标题
        SUBJECT = SUBJECT
        # 5> 邮件内容
        CONTENT = CONTENT
        
        # 创建邮件发送对象
        # 普通的邮件发送形式
        smtp_obj = smtplib.SMTP_SSL(HOST, port = 465)
        
        # 数据在传输过程中会被加密。
        # smtp_obj = smtplib.SMTP_SSL()
        
        # 需要进行发件人的认证，授权。
        # smtp_obj就是一个第三方客户端对象
        # smtp_obj.connect(host=HOST, port='25')
        smtp_obj.ehlo(HOST)
        # 如果使用第三方客户端登录，要求使用授权码，不能使用真实密码，防止密码泄露。
        res = smtp_obj.login(user=FROM, password=password)
        print('登录结果：',res)

        from email.mime.multipart import MIMEMultipart
        from email.mime.application import MIMEApplication
        from email.mime.text import MIMEText
        msg = MIMEMultipart()
        msg['From'] = FROM
        msg['To'] = ','.join(TO)
        msg['Subject'] = SUBJECT
        
        att = MIMEText(CONTENT, "plain", "utf-8")  # 使用UTF-8编码格式保证多语言的兼容性
        msg.attach(att)

        if attachs is not None:
            part = MIMEApplication(open(attachs, 'rb').read())
            part.add_header('Content-Disposition', 'attachment', filename='file_name.csv')
            msg.attach(part)
        # 发送邮件
        smtp_obj.sendmail(from_addr=FROM, to_addrs=TO, msg=msg.as_string()) 
        
        # msg = '\n'.join(['From: {}'.format(FROM), 'To: {}'.format(TO), 'Subject: {}'.format(SUBJECT), '', CONTENT])
        # smtp_obj.sendmail(from_addr=FROM, to_addrs=TO, msg=msg.encode('utf-8'))

    except Exception as E:
        print(E)

def send_to(Subject , messages = 'None', attach = None):
    send_email(FROM='yangt_1@126.com', TO =['781188496@qq.com'], CONTENT=messages, SUBJECT=Subject, attachs=attach)
    pass