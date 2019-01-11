import requests
from bs4 import BeautifulSoup
import json
import string
import os.path
import sys

def retrieveURL (page,genre): #function takes in a page number and genre, returns the soup for the web page
    url = 'https://www.boxofficemojo.com/genres/chart/?view=main&sort=gross&order=DESC&pagenum={}&id={}.htm'.format(page,genre) #format of main url
    r = requests.get(url)
    soup = BeautifulSoup(r.text,'html.parser')
    return soup


def get_movie_list(soup): #function takes in the soup of a url and creates a list of dictionaries for the movies in the url
    api_key = ' ' #api key for OMDB which enriches the movie data with plotlines, INSERT your own api key hear from OMDB API
    OMDB_endpoint = 'http://www.omdbapi.com/?apikey={}&t={}&plot=full' #OMDB endpoint
    main_div = soup.find('div', {'id': 'body'}) #finding main table in the Box Office Mojo URL
    main_table = main_div.find('h2')
    contents = main_table.findAll('tr')
    movies_list = [] #for the dictionaries
    for content in contents[3:-2]: #eliminating rows that do not have information about the movies
        if (len(content.findAll('td')) > 0):
            movies_dict = {} #dictionary for each movie
            movieName = content.findAll('td')[1].find('b')
            if movieName != None: #name of the movie
                name = movieName.text
                name = name.translate(name.maketrans('', '', ','))
                if '(' in name: #some movies have the year in the title which hinders the OMDB API
                    name = name.translate(name.maketrans('', '', string.digits)) #removing years from the title
                    name = name.translate(name.maketrans('', '', string.punctuation)) #removing punctuation
            else:
                continue
            totalGross = content.findAll('td')[3].find('b') #total gross of the movie
            if totalGross != None:
                gross = totalGross.text
                gross = gross.translate(gross.maketrans('', '', string.punctuation)) #removing commas
            else:
                continue
            openingDate = content.findAll('td')[7].find('a') #release date of movie
            if openingDate != None:
                date = openingDate.text
            else:
                continue
            movies_dict['Title'] = name #adding title to the dictionary for the movie
            movies_dict['Total Gross'] = gross #adding total gross to the dictionary for the movie
            movies_dict['Release Date'] = date #adding release date to the dictionary for the movie
            movies_list.append(movies_dict) #appending dictionary for this movie to the list of movies
    for movie in movies_list: #iterating through dictionaries of the movies in the list
        title = movie['Title'] #setting variable for the title of the movie
        plot_url = OMDB_endpoint.format(api_key, title) #formatting url to get the plot of the movie from OMDB API
        plot_response = requests.get(plot_url)
        if plot_response.json(): #condition to ensure json response exists
            plot_json = json.loads(plot_response.text)
            if plot_json['Response'] != 'False': #if response is False, OMDB does not have plot for movie
                plot = plot_json['Plot'] #assign plot variable to response of 'Plot' key in JSON response
                plot = plot.translate(plot.maketrans('', '', ',')) #remove commas for CSV writing
                movie['Plot'] = plot #adding to dictionary for movie
            else:
                continue
    return movies_list

def csv_writer(movies,output_file_name): #function writes out the CSV for the movies
    output_file = open(output_file_name,"a") #append new list of movies to existing CSV of movies
    fileEmpty = os.stat(output_file_name).st_size == 0 #how to recognize if a file is empty
    headers = movies[0].keys() #headers for the CSV file
    if fileEmpty: #only add headers to the CSV is the file is empty
        for header in headers: #write headers to the empty CSV
            output_file.write(header)
            output_file.write(',')
        output_file.write('\n')
    for movie in movies: #write each movie's values to the CSV
        for value in movie.values():
            output_file.write(value)
            output_file.write(',')
        output_file.write('\n')
    output_file.close()
