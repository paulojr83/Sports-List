# Sports List
# Project Display Example
#### Note: The screenshots on this page are just examples of one implementation of the minimal functionality. You are encouraged to redesign and strive for even better solutions.

The Item Catalog project consists of developing an application that provides a list of items within a variety of categories, as well as provide a user registration and authentication system.
In this sample project, the homepage displays all current categories along with the latest added items.

[http://localhost:8000/](http://localhost:8000/)
### Selecting a specific category shows you all the items available for that category.

![alt text](https://github.com/paulojr83/Sports-List/blob/master/8.PNG "all current categories")
[http://localhost:5000/category/2/item/](http://localhost:5000/category/2/item/)
### Selecting a specific item shows you specific information of that item.

[http://localhost:5000/sport/5/detail/](http://localhost:5000/sport/5/detail/)
Selecting a specific item shows you specific information of that item.

![alt text](https://github.com/paulojr83/Sports-List/blob/master/3.PNG "Json")
[http://localhost:5000/category/2/edit/](http://localhost:5000/category/2/edit/)
### After logging in, a user has the ability to add, update, or delete item info.

![alt text](https://github.com/paulojr83/Sports-List/blob/master/5.PNG "Json")
[http://localhost:5000/sport/5/edit/](http://localhost:5000/sport/5/edit/) (logged in)
### After logging in, a user has the ability to add, update, or delete item info.
### The application provides a JSON endpoint, at the very least.

![alt text](https://github.com/paulojr83/Sports-List/blob/master/7.PNG "Json")
[http://localhost:5000/category/catalog.json](http://localhost:5000/category/catalog.json)

![alt text](https://github.com/paulojr83/Sports-List/blob/master/9.PNG "Json")
[http://localhost:5000/category/category_id/catalog.json](http://localhost:5000/category/category_id/catalog.json)


## Webcasts for the Item Catalog Project
 Need some additional help getting started with the Item Catalog Project.
1. Set up the environment database: in your terminal > python sport_db.py 
 * For more information abou set up [Sqlalchemy](http://docs.sqlalchemy.org/en/latest/core/schema.html)

2. Run the project: in your terminal > python catalog.py access => than [http://localhost:5000/](http://localhost:5000/)

> These webcasts are recordings of live Q&A sessions and demos. As always, you should read the appropriate rubric for your project thoroughly before you begin work on any project and double check the rubric before submitting. The videos were made by Udacity's coaches. Think of them as extra supplemental materials.

#### The webcasts for the Item Catalog Project include:  
  * [Flask Templates](http://flask.pocoo.org/)
  * [Make Your App a Maximum Security Prison](https://pythonhosted.org/Flask-Security/)
  * [Deploying a Flask App with Heroku](https://www.youtube.com/watch?v=pmRT8QQLIqk)
  
