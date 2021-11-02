all:
	heroku container:push bot
	heroku container:release bot
