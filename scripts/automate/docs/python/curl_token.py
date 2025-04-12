curl -X POST \
    -d "grant_type=authorization_code" \
    -d "code=LqUYoKQ4txV5pQvEcgMyk2b98JZVX4" \
    -d "redirect_uri=http://localhost:8000/oauth2/callback" \
    -d "client_id=Eg76EoLFTkmHO5jh4H0RbWtFLjsMjVRNsDaaUOCR" \
    -d "client_secret=pbkdf2_sha256$870000$fwJnqC1sBbY7yQqzISlvPP$cAH4ZFzqrblBa8bbQVOuq+mdnPRmXflQ4xc9EKAg5rk=" \
    http://127.0.0.1:8000/o/token/