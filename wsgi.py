import sys

from GeneradorReportes import app

if __name__ == "__main__":
    sys.argv.append("--timeout")
    sys.argv.append('300')
    app.run(debug=True,host='0.0.0.0', port=6003)