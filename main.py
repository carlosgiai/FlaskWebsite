from website import create_app


# Youtube video explaining code
# https://www.youtube.com/watch?v=dam0GPOAvVI&ab_channel=TechWithTim

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
