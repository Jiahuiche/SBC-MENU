import intput_cbr 

def main():
    user_data = intput_cbr.get_user_restrictions()
    print(user_data)

    #Retrieval de casos más similares
    # Aquí iría el código para recuperar y mostrar los casos más similares

    # Adaptación de esos casos a las restricciones del usuario
    # Aquí iría el código para adaptar los casos recuperados a las preferencias del usuario

    #Preguntar al usuario si el menú adaptado le va bien
    #op_menu_respuesta = input("¿Le gusta el menú adaptado? (yes/no)").strip().lower()
    #if op_menu_respuesta == 'yes':
        #Guardar el caso adaptado en la base de datos
        #incrementar la utilidad de ese menú y método adaptación 
    #else:
        #otro ciclo de retrieval 
        #decrementar la utilidad de ese menú y método de adaptación


if __name__ == "__main__":
    main()