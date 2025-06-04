# Ejercicio Flask 1

Este proyecto es una aplicación CRUD desarrollada con **Flask** y conectada a una base de datos **MySQL**, orientada a la gestión de contactos. Incluye funciones de autenticación de usuarios, registro seguro con hash de contraseñas (usando `scrypt`), sesiones permanentes y una interfaz responsiva gracias a **Bootstrap 5**. Además, se incorporan temas visuales de [Bootswatch](https://bootswatch.com/), permitiendo una personalización sencilla del estilo de la aplicación.

La aplicación permite a los usuarios registrados:
- Ver una lista de contactos guardados.
- Agregar nuevos contactos con nombre, teléfono y correo.
- Editar o eliminar contactos existentes.

El acceso está protegido por sesión. Los usuarios deben iniciar sesión para poder utilizar la funcionalidad CRUD. Las credenciales se almacenan de forma segura y se valida cada operación importante mediante logs y mensajes flash. También se incorpora un modo oscuro que puede alternarse dinámicamente y se guarda por sesión.
