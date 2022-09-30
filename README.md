## Sparco Demo

Create a user platform consisting of an Android App, Restful API & Web Portal.


The platform should allow users to:

1. Sign up

2. Sign in

3. Carry out CRUD operations on their profile

4. View list of profiles of other users(if user opted in for their profile to be public).

5. View detailed profiles

5. Search for public profiles(Full text search should be implemented without using any third party)


The user data should at minimum consist of:


- first name

- last name

- email (verification should be implemented)

- phone number (verification should be implemented)

- user image


The platform should have two user types:


1. Standard Users - These should only be able to perform CRUD operation on the profiles.

2. Users with elevated privileges - These should be able to perform CRUD operations on all users, this includes grant elevated privileges to other users


Build the mobile app using a framework of your choosing, the REST API using Flask (Let me know f it's easier for you to use to different language and framework), Postgres, SQLAlchemy for ORM and authentication should use JWT. The web portal should use React JS. 


The application(web portal & mobile app) should have 4 routes and pages:


1 - Login - For Authenticating users through email and password.

2 - Registration - Users should provide first name, last name, email and phone number.

3 - Profile - Should display the users first name, last name, email, phone and role

4 - User List - should display the list of users.