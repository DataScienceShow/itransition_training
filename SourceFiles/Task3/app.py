from flask import Flask, request

app = Flask(__name__)

@app.route('/ziyodullofficial_gmail_com', methods=['GET'])
def lcm_endpoint():
    x = request.args.get('x', '')
    y = request.args.get('y', '')
    try:
        x_int = int(x)
        y_int = int(y)
        if x_int < 0 or y_int < 0:
            return 'NaN'
    except (ValueError, TypeError):
        return 'NaN'
    if x_int == 0 or y_int == 0:
        return '0'
    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a
    def lcm(a, b):
        return abs(a * b) // gcd(a, b)
    return str(lcm(x_int, y_int))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
