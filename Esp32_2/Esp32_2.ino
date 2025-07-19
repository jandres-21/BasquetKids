#include <WiFi.h>
#include <PubSubClient.h>
#include <FastLED.h>
#include <ArduinoJson.h>

const char* ssid = "Grupo_5";
const char* password = "123cuatro";
const char* mqtt_server = "192.168.1.104";
const int mqtt_port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

const char* TOPIC_LED_CENTRO = "led2/control";
const char* TOPIC_LED_IZQUIERDO = "led3/control";
const char* TOPIC_PIEZO = "sensor/piezo_mayor";
const char* TOPIC_ANIMACION = "animacion/aro";
const char* TOPIC_ANIMACION_ESTADO = "animacion/estado";

#define NUM_LEDS_CENTRO 16
#define DATA_PIN_CENTRO 27
#define NUM_LEDS_IZQUIERDO 16
#define DATA_PIN_IZQUIERDO 26
CRGB ledsCentro[NUM_LEDS_CENTRO];
CRGB ledsIzquierdo[NUM_LEDS_IZQUIERDO];

#define BRILLO 76
#define UMBRAL_CENTRO 100
#define UMBRAL_IZQUIERDO 300
#define TIEMPO_PIEZO_LED 4000
#define TIEMPO_DEBOUNCE 200
#define TIEMPO_ENCESTE 4000

#define PIEZO_PIN_CENTRO 34
#define PIEZO_PIN_IZQUIERDO 32
#define PIN_ENCESTE_IN 25

unsigned long tiempoGolpeCentro = 0;
unsigned long tiempoGolpeIzquierdo = 0;
unsigned long ultimoGolpeCentro = 0;
unsigned long ultimoGolpeIzquierdo = 0;
bool piezoCentroActivo = false;
bool piezoIzquierdoActivo = false;

bool encesteActivo = false;
unsigned long tiempoEnceste = 0;
bool encestePrevio = false;

uint8_t hue = 0;

uint8_t rCentro = 255, gCentro = 0, bCentro = 0;
uint8_t rIzquierdo = 0, gIzquierdo = 0, bIzquierdo = 255;

bool destelloEncendido = false;
String animacionEnceste = "destello_exitoso";

bool ledCentroEncendidoMQTT = false;
unsigned long tiempoEncendidoCentro = 0;
bool ledCentroHabilitado = false;

bool ledIzquierdoEncendidoMQTT = false;
unsigned long tiempoEncendidoIzquierdo = 0;
bool ledIzquierdoHabilitado = false;

const unsigned long DURACION_LED_ON = 4000;
bool animacionesHabilitadas = true;

void conectarWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Conectando a WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi conectado");
}

void conectarMQTT() {
  while (!client.connected()) {
    Serial.print("Conectando a MQTT...");
    if (client.connect("ESP32_LED_PIEZOS")) {
      Serial.println("✅ MQTT conectado");
      client.subscribe(TOPIC_LED_CENTRO);
      client.subscribe(TOPIC_LED_IZQUIERDO);
      client.subscribe(TOPIC_ANIMACION);
      client.subscribe(TOPIC_ANIMACION_ESTADO);
    } else {
      Serial.print("❌ error: ");
      Serial.println(client.state());
      delay(1000);
    }
  }
}

void setColor(CRGB* leds, int num, uint8_t rr, uint8_t gg, uint8_t bb) {
  for (int i = 0; i < num; i++) leds[i] = CRGB(rr, gg, bb);
  FastLED.show();
}

void apagarLedCentro() {
  setColor(ledsCentro, NUM_LEDS_CENTRO, 0, 0, 0);
  ledCentroEncendidoMQTT = false;
  Serial.println("💡 LED Centro apagado");
}

void apagarLedIzquierdo() {
  setColor(ledsIzquierdo, NUM_LEDS_IZQUIERDO, 0, 0, 0);
  ledIzquierdoEncendidoMQTT = false;
  Serial.println("💡 LED Izquierdo apagado");
}

void ejecutarAnimacion(String nombre) {
  if (nombre == "arcoiris_brillante") {
    if (ledCentroHabilitado) fill_rainbow(ledsCentro, NUM_LEDS_CENTRO, hue, 7);
    if (ledIzquierdoHabilitado) fill_rainbow(ledsIzquierdo, NUM_LEDS_IZQUIERDO, hue, 7);
    FastLED.show();
    hue++;
  } else if (nombre == "destello_exitoso") {
    CRGB color = destelloEncendido ? CRGB::Yellow : CRGB::Black;
    if (ledCentroHabilitado) {
      for (int i = 0; i < NUM_LEDS_CENTRO; i++) ledsCentro[i] = color;
    } else {
      for (int i = 0; i < NUM_LEDS_CENTRO; i++) ledsCentro[i] = CRGB::Black;
    }
    if (ledIzquierdoHabilitado) {
      for (int i = 0; i < NUM_LEDS_IZQUIERDO; i++) ledsIzquierdo[i] = color;
    } else {
      for (int i = 0; i < NUM_LEDS_IZQUIERDO; i++) ledsIzquierdo[i] = CRGB::Black;
    }
    FastLED.show();
    destelloEncendido = !destelloEncendido;
  } else {
    setColor(ledsCentro, NUM_LEDS_CENTRO, 0, 0, 0);
    setColor(ledsIzquierdo, NUM_LEDS_IZQUIERDO, 0, 0, 0);
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String mensaje = "";
  for (unsigned int i = 0; i < length; i++) mensaje += (char)payload[i];
  mensaje.trim();

  Serial.print("Mensaje recibido en topic ");
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(mensaje);

  StaticJsonDocument<128> doc;
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error) {
    // Manejo de mensajes simples (ON/OFF)
    if (String(topic) == TOPIC_LED_CENTRO) {
      if (mensaje.equalsIgnoreCase("ON")) {
        ledCentroHabilitado = true;
        setColor(ledsCentro, NUM_LEDS_CENTRO, rCentro, gCentro, bCentro);
        ledCentroEncendidoMQTT = true;
        tiempoEncendidoCentro = millis();
      } else if (mensaje.equalsIgnoreCase("OFF")) {
        ledCentroHabilitado = false;
        apagarLedCentro();
      }
    } else if (String(topic) == TOPIC_LED_IZQUIERDO) {
      if (mensaje.equalsIgnoreCase("ON")) {
        ledIzquierdoHabilitado = true;
        setColor(ledsIzquierdo, NUM_LEDS_IZQUIERDO, rIzquierdo, gIzquierdo, bIzquierdo);
        ledIzquierdoEncendidoMQTT = true;
        tiempoEncendidoIzquierdo = millis();
      } else if (mensaje.equalsIgnoreCase("OFF")) {
        ledIzquierdoHabilitado = false;
        apagarLedIzquierdo();
      }
    } else if (String(topic) == TOPIC_ANIMACION_ESTADO) {
      animacionesHabilitadas = mensaje.equalsIgnoreCase("ON");
    }
  } else {
    // Solo aceptar animaciones "destello" y "arcoiris"
    if (String(topic) == TOPIC_ANIMACION && doc.containsKey("animation")) {
      String anim = String((const char*)doc["animation"]);
      anim.toLowerCase();

      if (anim == "destello") {
        animacionEnceste = "destello_exitoso";
        Serial.println("🎨 Animación cambiada a: destello");
      }
      else if (anim == "arcoiris") {
        animacionEnceste = "arcoiris_brillante";
        Serial.println("🎨 Animación cambiada a: arcoiris");
      }
      else {
        Serial.println("⚠ Animación no permitida, solo 'destello' o 'arcoiris'");
      }
    }
    // Manejar colores LED si llegan en JSON
    else if ((String(topic) == TOPIC_LED_CENTRO || String(topic) == TOPIC_LED_IZQUIERDO) && doc.containsKey("r")) {
      uint8_t rr = doc["r"];
      uint8_t gg = doc["g"];
      uint8_t bb = doc["b"];

      if (String(topic) == TOPIC_LED_CENTRO) {
        rCentro = rr; gCentro = gg; bCentro = bb;
        if (ledCentroHabilitado) {
          setColor(ledsCentro, NUM_LEDS_CENTRO, rCentro, gCentro, bCentro);
          ledCentroEncendidoMQTT = true;
          tiempoEncendidoCentro = millis();
        }
      } else {
        rIzquierdo = rr; gIzquierdo = gg; bIzquierdo = bb;
        if (ledIzquierdoHabilitado) {
          setColor(ledsIzquierdo, NUM_LEDS_IZQUIERDO, rIzquierdo, gIzquierdo, bIzquierdo);
          ledIzquierdoEncendidoMQTT = true;
          tiempoEncendidoIzquierdo = millis();
        }
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  FastLED.addLeds<WS2812B, DATA_PIN_CENTRO, GRB>(ledsCentro, NUM_LEDS_CENTRO);
  FastLED.addLeds<WS2812B, DATA_PIN_IZQUIERDO, GRB>(ledsIzquierdo, NUM_LEDS_IZQUIERDO);
  FastLED.setBrightness(BRILLO);
  setColor(ledsCentro, NUM_LEDS_CENTRO, 0, 0, 0);
  setColor(ledsIzquierdo, NUM_LEDS_IZQUIERDO, 0, 0, 0);

  pinMode(PIEZO_PIN_CENTRO, INPUT);
  pinMode(PIEZO_PIN_IZQUIERDO, INPUT);
  pinMode(PIN_ENCESTE_IN, INPUT);

  conectarWiFi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) conectarMQTT();
  client.loop();

  unsigned long ahora = millis();
  int piezoCentro = analogRead(PIEZO_PIN_CENTRO);
  int piezoIzquierdo = analogRead(PIEZO_PIN_IZQUIERDO);
  bool encesteSignal = digitalRead(PIN_ENCESTE_IN) == HIGH;

  if (ledCentroEncendidoMQTT && (ahora - tiempoEncendidoCentro > DURACION_LED_ON)) apagarLedCentro();
  if (ledIzquierdoEncendidoMQTT && (ahora - tiempoEncendidoIzquierdo > DURACION_LED_ON)) apagarLedIzquierdo();

  if (encesteSignal && !encestePrevio && !encesteActivo) {
    Serial.println("🏀 Enceste detectado (señal pin)");
    encesteActivo = true;
    tiempoEnceste = ahora;
    encestePrevio = true;
  }
  if (!encesteSignal) encestePrevio = false;

  // Ejecutar animación si están habilitadas
  if (encesteActivo && animacionesHabilitadas) {
    ejecutarAnimacion(animacionEnceste);
  }

  // Este bloque siempre se ejecuta para liberar el enceste
  if (encesteActivo && (ahora - tiempoEnceste > TIEMPO_ENCESTE)) {
    encesteActivo = false;
    if (!ledCentroEncendidoMQTT) setColor(ledsCentro, NUM_LEDS_CENTRO, 0, 0, 0);
    if (!ledIzquierdoEncendidoMQTT) setColor(ledsIzquierdo, NUM_LEDS_IZQUIERDO, 0, 0, 0);
  }

  // Piezo solo si no hay animación de enceste activa
  if (!encesteActivo) {
    if (piezoIzquierdo > UMBRAL_IZQUIERDO && (ahora - ultimoGolpeIzquierdo > TIEMPO_DEBOUNCE)) {
      ultimoGolpeIzquierdo = ahora;
      piezoIzquierdoActivo = true;
      tiempoGolpeIzquierdo = ahora;
      client.publish(TOPIC_PIEZO, "izquierdo");
      if (ledIzquierdoHabilitado) setColor(ledsIzquierdo, NUM_LEDS_IZQUIERDO, rIzquierdo, gIzquierdo, bIzquierdo);
    }
    if (piezoIzquierdoActivo && (ahora - tiempoGolpeIzquierdo > TIEMPO_PIEZO_LED)) {
      piezoIzquierdoActivo = false;
      if (ledIzquierdoHabilitado) setColor(ledsIzquierdo, NUM_LEDS_IZQUIERDO, 0, 0, 0);
    }

    if (piezoCentro > UMBRAL_CENTRO && (ahora - ultimoGolpeCentro > TIEMPO_DEBOUNCE)) {
      ultimoGolpeCentro = ahora;
      piezoCentroActivo = true;
      tiempoGolpeCentro = ahora;
      client.publish(TOPIC_PIEZO, "centro");
      if (ledCentroHabilitado) setColor(ledsCentro, NUM_LEDS_CENTRO, rCentro, gCentro, bCentro);
    }
    if (piezoCentroActivo && (ahora - tiempoGolpeCentro > TIEMPO_PIEZO_LED)) {
      piezoCentroActivo = false;
      if (ledCentroHabilitado) setColor(ledsCentro, NUM_LEDS_CENTRO, 0, 0, 0);
    }
  }

  delay(50);
}