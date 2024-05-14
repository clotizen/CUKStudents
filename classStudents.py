from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests
import uuid
import json

app = Flask(__name__)

class catlog():
    def __init__(self):
        self.session = ''
        self.req_login = ''

    def login(self, userId, userPassword):
        sessid_1 = str(uuid.uuid4())
        sessid_2 = str(uuid.uuid4())

        sessid = sessid_1.replace('-', '') + sessid_2.replace('-', '')

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0'}
        cookies = {'SESSION_SSO': sessid + '.c3R3X2RvbWFpbi9zc29fMg=='}

        re = requests.get('https://uportal.catholic.ac.kr/sso/jsp/sso/ip/login_form.jsp', headers=headers,
                          cookies=cookies)

        html = re.text
        soup = BeautifulSoup(html, 'html.parser')
        samlRequest = soup.find('input', {'name': 'samlRequest'}).get('value')

        data1 = {'userId': userId, 'password': userPassword, 'samlRequest': samlRequest}

        req = requests.post('https://uportal.catholic.ac.kr/sso/processAuthnResponse.do', headers=headers,
                            cookies=cookies, data=data1)

        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        SAMLResponse = soup.find('input', {'name': 'SAMLResponse'}).get('value')

        data2 = {'SAMLResponse': SAMLResponse}

        self.session = requests.session()
        self.req_login = self.session.post('https://uportal.catholic.ac.kr/portal/login/login.ajax', headers=headers,
                                           data=data2)

    def find(self, id, no, json_data):
        try:
            for i in range(len(json_data["DS_CURR_OPSB010"])):
                if json_data["DS_CURR_OPSB010"][i]["sbjtNo"] == id and json_data["DS_CURR_OPSB010"][i]['clssNo'] == no:
                    cnt = json_data["DS_CURR_OPSB010"][i]['tlsnAplyRcnt']  # 신청인원
                    cnt2 = json_data["DS_CURR_OPSB010"][i]['tlsnLmtRcnt']  # 제한인원
                    cnt3 = json_data["DS_CURR_OPSB010"][i]['sbjtKorNm']  # 과목명
                    return cnt, cnt2, cnt3
        except:
            return 'Error', 'Error', 'Error'

    def get_json(self, year, semester):
        html = self.req_login.text
        soup = BeautifulSoup(html, 'html.parser')
        csrf = soup.find('meta', {'id': '_csrf'}).get('content')

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
                   'Accept': 'application/json, text/javascript, */*; q=0.01',
                   'Accept-Encoding':'gzip, deflate, br',
                   'Accept-Language':'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                   'X-CSRF-TOKEN': csrf,
                   'X-Requested-With': 'XMLHttpRequest',
                   'Origin': 'https://uportal.catholic.ac.kr',
                   'Referer': 'https://uportal.catholic.ac.kr/stw/scsr/scoo/scooOpsbOpenSubjectInq.do'
                   }

        data = {'quatFg': 'INQ', 'posiFg': semester, 'openYyyy': year, 'openShtm': semester, 'campFg': 'M', 'sustCd': '%',
                'corsCd': '|', 'danFg': '', 'pobtFgCd': '%'}

        cookies = {'UCUPS_PT_SESSION': self.session.cookies.get_dict()['UCUPS_PT_SESSION']}

        return requests.post('https://uportal.catholic.ac.kr/stw/scsr/scoo/findOpsbOpenSubjectInq.json',
                             headers=headers, cookies=cookies, data=data).json()

@app.route('/classStudents', methods=['GET'])
def get_class_students():
    try:
        subj = request.args.get('subjNo')
        no = request.args.get('classNo')
        userId = request.args.get('userId')
        userPw = request.args.get('userPw')
        year = request.args.get('year')
        semester = request.args.get('semester')

        catApi = catlog()
        catApi.login(userId, userPw)
        jsonData = catApi.get_json(year, semester)
        now, limit, className = catApi.find(subj, no, jsonData)
        resMsg = {
            "totalNum": limit,
            "nowNum": now,
            "className": className
        }
        return jsonify(resMsg)
    except Exception as e:
        errMsg = {
            "errCode": 21,
            "message": f"트리니티 정보 조회에 실패하였습니다: {str(e)}"
        }
        return jsonify(errMsg), 400

if __name__ == '__main__':
    app.run(debug=True)
