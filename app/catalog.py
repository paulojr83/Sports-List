from router import *

if __name__ == '__main__':
    app.secret_key = 'some_secret'
    app.run(debug=True)