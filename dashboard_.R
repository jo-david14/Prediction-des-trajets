# ==============================================================================
# 0. INSTALLATION AUTOMATIQUE DES PACKAGES (si nécessaire)
# ==============================================================================
required_packages <- c("shiny", "bslib", "httr2", "jsonlite", "bsicons")

missing_packages <- required_packages[!(required_packages %in% installed.packages()[, "Package"])]

if (length(missing_packages) > 0) {
  message("Installation des packages manquants : ", paste(missing_packages, collapse = ", "))
  install.packages(missing_packages, dependencies = TRUE)
}

# Chargement des bibliothèques
library(shiny)
library(bslib)
library(httr2)
library(jsonlite)
library(bsicons)

# ==============================================================================
# 1. INTERFACE UTILISATEUR (UI)
# ==============================================================================
ui <- page_sidebar(
  title = "NYC Taxi Fare Predictor",
  theme = bs_theme(version = 5, bootswatch = "flatly"),
  
  # Barre latérale pour les entrées utilisateur
  sidebar = sidebar(
    title = "Paramètres de la course",
    
    numericInput("pickup_lng", "Longitude de départ (Pickup)", value = -73.9857, min = -74.3, max = -73.6),
    numericInput("pickup_lat", "Latitude de départ (Pickup)", value = 40.7484, min = 40.4, max = 41.0),
    hr(),
    numericInput("dropoff_lng", "Longitude d'arrivée (Dropoff)", value = -73.9772, min = -74.3, max = -73.6),
    numericInput("dropoff_lat", "Latitude d'arrivée (Dropoff)", value = 40.7527, min = 40.4, max = 41.0),
    hr(),
    
    sliderInput("passengers", "Nombre de passagers", min = 1, max = 6, value = 1, step = 1),
    
    selectInput("hour", "Heure de prise en charge", choices = 0:23, selected = 14),
    selectInput("month", "Mois", choices = 1:12, selected = 6),
    selectInput("year", "Année", choices = 2014:2018, selected = 2026),
    selectInput("day_of_week", "Jour de la semaine", 
                choices = c("Lundi" = 0, "Mardi" = 1, "Mercredi" = 2, "Jeudi" = 3, 
                            "Vendredi" = 4, "Samedi" = 5, "Dimanche" = 6), 
                selected = 2),
    
    actionButton("predict_btn", "Estimer le prix", class = "btn-primary w-100 mt-3")
  ),
  
  # Contenu principal (Affichage des résultats)
  card(
    card_header("Résultat de l'estimation par l'IA (LightGBM)"),
    layout_column_wrap(
      width = 1/2,
      value_box(
        title = "Prix estimé (USD)",
        value = textOutput("fare_display"),
        showcase = bs_icon("currency-dollar"),
        theme = "success"
      ),
      value_box(
        title = "Distance calculée",
        value = textOutput("distance_display"),
        showcase = bs_icon("geo-alt"),
        theme = "info"
      )
    ),
    card_body(
      markdown("### Détails de la sectorisation"),
      verbatimTextOutput("boroughs_display")
    )
  )
)

# ==============================================================================
# 2. LOGIQUE SERVEUR (SERVER)
# ==============================================================================
server <- function(input, output, session) {
  
  # URL de ton API FastAPI locale (qui tourne dans Docker)
  api_url <- "http://localhost:8000/predict"
  
  # Réactivité : Déclenché uniquement quand on clique sur le bouton "Estimer le prix"
  prediction_data <- eventReactive(input$predict_btn, {
    
    # Préparation du dictionnaire de données (Payload JSON)
    body_data <- list(
      pickup_longitude = as.numeric(input$pickup_lng),
      pickup_latitude = as.numeric(input$pickup_lat),
      dropoff_longitude = as.numeric(input$dropoff_lng),
      dropoff_latitude = as.numeric(input$dropoff_lat),
      passenger_count = as.integer(input$passengers),
      pickup_hour = as.integer(input$hour),
      pickup_month = as.integer(input$month),
      pickup_year = as.integer(input$year),
      pickup_day_of_week = as.integer(input$day_of_week)
    )
    
    # Envoi de la requête POST à l'API Docker avec httr2
    tryCatch({
      req <- request(api_url) %>%
        req_body_json(body_data) %>%
        req_error(is_error = function(resp) FALSE) # Évite le crash si l'API répond une erreur
      
      resp <- req_perform(req)
      
      # Si l'API renvoie un succès (Code HTTP 200)
      if (resp_status(resp) == 200) {
        resp_body_json(resp)
      } else {
        list(error = paste("Erreur API : Statut", resp_status(resp)))
      }
    }, error = function(e) {
      list(error = "Impossible de contacter l'API. Assure-toi que ton conteneur Docker tourne bien sur le port 8000.")
    })
  })
  
  # 1. Affichage du prix
  output$fare_display <- renderText({
    res <- prediction_data()
    if (!is.null(res$error)) {
      return("Erreur")
    }
    paste0(res$predicted_fare_usd, " $")
  })
  
  # 2. Affichage de la distance
  output$distance_display <- renderText({
    res <- prediction_data()
    if (!is.null(res$error)) {
      return("--")
    }
    paste0(res$distance_km, " km")
  })
  
  # 3. Affichage des Boroughs détectés
  output$boroughs_display <- renderPrint({
    res <- prediction_data()
    if (!is.null(res$error)) {
      cat(res$error)
    } else {
      cat("Quartier de départ :", res$pickup_borough, "\n")
      cat("Quartier d'arrivée :", res$dropoff_borough)
    }
  })
}

# ==============================================================================
# 3. LANCEMENT DE L'APPLICATION
# ==============================================================================
shinyApp(ui = ui, server = server)