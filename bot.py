import os
import random
import re
import unicodedata
from typing import Dict, List, Tuple, Any, Optional

import discord
from discord.ext import commands, tasks
import asyncio

VERSION_BOT = "4.0.2"

# =========================
# CONFIGURA ESTAS IDS
# =========================
CANAL_BOT_ID = 1487601532273954907
FORO_ID = 1487607124388216832

# Canal donde se usarán las encuestas
CANAL_ENCUESTAS_ID = 1488382310528188536

# Canal donde el bot dejará registro de quién respondió cada encuesta
CANAL_RESULTADOS_ENCUESTAS_ID = 1488382682831524041

TOKEN = os.getenv("DISCORD_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# UTILIDADES
# =========================
def normalizar(texto: str) -> str:
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto

def contiene_palabra(texto: str, palabra: str) -> bool:
    texto = normalizar(texto)
    palabra = normalizar(palabra)
    patron = rf"\b{re.escape(palabra)}\b"
    return re.search(patron, texto) is not None

def contiene_alguna(texto: str, opciones: List[str]) -> Tuple[bool, str]:
    for opcion in opciones:
        if contiene_palabra(texto, opcion):
            return True, opcion
    return False, ""

def limpiar_codigo_pseint(codigo: str) -> str:
    lineas = [line.rstrip() for line in codigo.splitlines()]
    while lineas and not lineas[0].strip():
        lineas.pop(0)
    while lineas and not lineas[-1].strip():
        lineas.pop()
    return "\n".join(lineas)

def detectar_tema_por_numero(numero: int) -> str:
    if 1 <= numero <= 20:
        return "secuencial"
    if 21 <= numero <= 40:
        return "condicional"
    if 41 <= numero <= 55:
        return "segun"
    if 56 <= numero <= 80:
        return "ciclos"
    return "azar"

def crear_ejercicio(
    id_: str,
    enunciado: str,
    tipo: str,
    debe_tener: List[str],
    debe_tener_una: List[str],
    puede_tener: List[str],
    evitar: List[str],
    pista: str,
    solucion: str,
) -> Dict[str, Any]:
    return {
        "id": id_,
        "enunciado": enunciado,
        "tipo_principal": tipo,
        "debe_tener": debe_tener,
        "debe_tener_una": debe_tener_una,
        "puede_tener": puede_tener,
        "evitar": evitar,
        "pista": pista,
        "solucion": solucion,
    }

BANCO_100: List[Dict[str, Any]] = [
    {
        "numero": 1,
        "titulo": "Mostrar un mensaje",
        "enunciado": "Mostrar en pantalla el mensaje \"Hola mundo\".",
        "solucion": "Proceso Ejercicio1\n\n    Escribir \"Hola mundo\"\n\nFinProceso"
    },
    {
        "numero": 2,
        "titulo": "Pedir y mostrar un nombre",
        "enunciado": "Pedir el nombre del usuario y luego mostrarlo.",
        "solucion": "Proceso Ejercicio2\n\n    Definir nombre Como Cadena\n\n    Escribir \"Ingrese su nombre:\"\n\n    Leer nombre\n\n    Escribir \"Hola, \", nombre\n\nFinProceso"
    },
    {
        "numero": 3,
        "titulo": "Sumar dos números",
        "enunciado": "Pedir dos números y mostrar su suma.",
        "solucion": "Proceso Ejercicio3\n\n    Definir a, b, suma Como Real\n\n    Escribir \"Ingrese el primer numero:\"\n\n    Leer a\n\n    Escribir \"Ingrese el segundo numero:\"\n\n    Leer b\n\n    suma <- a + b\n\n    Escribir \"La suma es: \", suma\n\nFinProceso"
    },
    {
        "numero": 4,
        "titulo": "Restar dos números",
        "enunciado": "Pedir dos números y mostrar la resta.",
        "solucion": "Proceso Ejercicio4\n\n    Definir a, b, resta Como Real\n\n    Escribir \"Ingrese el primer numero:\"\n\n    Leer a\n\n    Escribir \"Ingrese el segundo numero:\"\n\n    Leer b\n\n    resta <- a - b\n\n    Escribir \"La resta es: \", resta\n\nFinProceso"
    },
    {
        "numero": 5,
        "titulo": "Multiplicar dos números",
        "enunciado": "Pedir dos números y mostrar la multiplicación.",
        "solucion": "Proceso Ejercicio5\n\n    Definir a, b, producto Como Real\n\n    Escribir \"Ingrese el primer numero:\"\n\n    Leer a\n\n    Escribir \"Ingrese el segundo numero:\"\n\n    Leer b\n\n    producto <- a * b\n\n    Escribir \"La multiplicacion es: \", producto\n\nFinProceso"
    },
    {
        "numero": 6,
        "titulo": "Dividir dos números",
        "enunciado": "Pedir dos números y mostrar la división.",
        "solucion": "Proceso Ejercicio6\n\n    Definir a, b, division Como Real\n\n    Escribir \"Ingrese el primer numero:\"\n\n    Leer a\n\n    Escribir \"Ingrese el segundo numero:\"\n\n    Leer b\n\n    division <- a / b\n\n    Escribir \"La division es: \", division\n\nFinProceso"
    },
    {
        "numero": 7,
        "titulo": "Área de un cuadrado",
        "enunciado": "Pedir el lado de un cuadrado y calcular su área.",
        "solucion": "Proceso Ejercicio7\n\n    Definir lado, area Como Real\n\n    Escribir \"Ingrese el lado del cuadrado:\"\n\n    Leer lado\n\n    area <- lado * lado\n\n    Escribir \"El area es: \", area\n\nFinProceso"
    },
    {
        "numero": 8,
        "titulo": "Perímetro de un rectángulo",
        "enunciado": "Pedir base y altura de un rectángulo y calcular su perímetro.",
        "solucion": "Proceso Ejercicio8\n\n    Definir base, altura, perimetro Como Real\n\n    Escribir \"Ingrese la base:\"\n\n    Leer base\n\n    Escribir \"Ingrese la altura:\"\n\n    Leer altura\n\n    perimetro <- 2 * (base + altura)\n\n    Escribir \"El perimetro es: \", perimetro\n\nFinProceso"
    },
    {
        "numero": 9,
        "titulo": "Área de un triángulo",
        "enunciado": "Pedir base y altura de un triángulo y calcular su área.",
        "solucion": "Proceso Ejercicio9\n\n    Definir base, altura, area Como Real\n\n    Escribir \"Ingrese la base:\"\n\n    Leer base\n\n    Escribir \"Ingrese la altura:\"\n\n    Leer altura\n\n    area <- (base * altura) / 2\n\n    Escribir \"El area es: \", area\n\nFinProceso"
    },
    {
        "numero": 10,
        "titulo": "Promedio de tres notas",
        "enunciado": "Pedir tres notas y mostrar el promedio.",
        "solucion": "Proceso Ejercicio10\n\n    Definir n1, n2, n3, promedio Como Real\n\n    Escribir \"Ingrese nota 1:\"\n\n    Leer n1\n\n    Escribir \"Ingrese nota 2:\"\n\n    Leer n2\n\n    Escribir \"Ingrese nota 3:\"\n\n    Leer n3\n\n    promedio <- (n1 + n2 + n3) / 3\n\n    Escribir \"El promedio es: \", promedio\n\nFinProceso"
    },
    {
        "numero": 11,
        "titulo": "Número siguiente",
        "enunciado": "Pedir un número y mostrar el siguiente.",
        "solucion": "Proceso Ejercicio11\n\n    Definir n Como Entero\n\n    Escribir \"Ingrese un numero:\"\n\n    Leer n\n\n    Escribir \"El siguiente es: \", n + 1\n\nFinProceso"
    },
    {
        "numero": 12,
        "titulo": "Número anterior",
        "enunciado": "Pedir un número y mostrar el anterior.",
        "solucion": "Proceso Ejercicio12\n\n    Definir n Como Entero\n\n    Escribir \"Ingrese un numero:\"\n\n    Leer n\n\n    Escribir \"El anterior es: \", n - 1\n\nFinProceso"
    },
    {
        "numero": 13,
        "titulo": "Doble y triple",
        "enunciado": "Pedir un número y mostrar su doble y su triple.",
        "solucion": "Proceso Ejercicio13\n\n    Definir n Como Real\n\n    Escribir \"Ingrese un numero:\"\n\n    Leer n\n\n    Escribir \"Doble: \", n * 2\n\n    Escribir \"Triple: \", n * 3\n\nFinProceso"
    },
    {
        "numero": 14,
        "titulo": "Metros a centímetros",
        "enunciado": "Pedir metros y convertirlos a centímetros.",
        "solucion": "Proceso Ejercicio14\n\n    Definir metros, centimetros Como Real\n\n    Escribir \"Ingrese metros:\"\n\n    Leer metros\n\n    centimetros <- metros * 100\n\n    Escribir \"Centimetros: \", centimetros\n\nFinProceso"
    },
    {
        "numero": 15,
        "titulo": "Horas a minutos",
        "enunciado": "Pedir horas y convertirlas a minutos.",
        "solucion": "Proceso Ejercicio15\n\n    Definir horas, minutos Como Entero\n\n    Escribir \"Ingrese horas:\"\n\n    Leer horas\n\n    minutos <- horas * 60\n\n    Escribir \"Minutos: \", minutos\n\nFinProceso"
    },
    {
        "numero": 16,
        "titulo": "Calcular IVA",
        "enunciado": "Pedir el precio de un producto y mostrar el precio más IVA del 19%.",
        "solucion": "Proceso Ejercicio16\n\n    Definir precio, iva, total Como Real\n\n    Escribir \"Ingrese el precio:\"\n\n    Leer precio\n\n    iva <- precio * 0.19\n\n    total <- precio + iva\n\n    Escribir \"IVA: \", iva\n\n    Escribir \"Total: \", total\n\nFinProceso"
    },
    {
        "numero": 17,
        "titulo": "Descuento porcentual",
        "enunciado": "Pedir un precio y un porcentaje de descuento. Mostrar el total a pagar.",
        "solucion": "Proceso Ejercicio17\n\n    Definir precio, porcentaje, descuento, total Como Real\n\n    Escribir \"Ingrese el precio:\"\n\n    Leer precio\n\n    Escribir \"Ingrese el porcentaje de descuento:\"\n\n    Leer porcentaje\n\n    descuento <- precio * porcentaje / 100\n\n    total <- precio - descuento\n\n    Escribir \"Descuento: \", descuento\n\n    Escribir \"Total a pagar: \", total\n\nFinProceso"
    },
    {
        "numero": 18,
        "titulo": "Promedio ponderado simple",
        "enunciado": "Pedir dos notas: una vale 40% y la otra 60%. Mostrar el promedio final.",
        "solucion": "Proceso Ejercicio18\n\n    Definir n1, n2, final Como Real\n\n    Escribir \"Ingrese nota 1:\"\n\n    Leer n1\n\n    Escribir \"Ingrese nota 2:\"\n\n    Leer n2\n\n    final <- n1 * 0.40 + n2 * 0.60\n\n    Escribir \"Promedio final: \", final\n\nFinProceso"
    },
    {
        "numero": 19,
        "titulo": "Convertir días a horas",
        "enunciado": "Pedir una cantidad de días y convertirla a horas.",
        "solucion": "Proceso Ejercicio19\n\n    Definir dias, horas Como Entero\n\n    Escribir \"Ingrese dias:\"\n\n    Leer dias\n\n    horas <- dias * 24\n\n    Escribir \"Horas: \", horas\n\nFinProceso"
    },
    {
        "numero": 20,
        "titulo": "Intercambiar valores",
        "enunciado": "Pedir dos números e intercambiar sus valores usando una variable auxiliar.",
        "solucion": "Proceso Ejercicio20\n\n    Definir a, b, aux Como Entero\n\n    Escribir \"Ingrese a:\"\n\n    Leer a\n\n    Escribir \"Ingrese b:\"\n\n    Leer b\n\n    aux <- a\n\n    a <- b\n\n    b <- aux\n\n    Escribir \"Ahora a vale: \", a\n\n    Escribir \"Ahora b vale: \", b\n\nFinProceso"
    },
    {
        "numero": 21,
        "titulo": "Positivo, negativo o cero",
        "enunciado": "Pedir un número y decir si es positivo, negativo o cero.",
        "solucion": "Proceso Ejercicio21\n\n    Definir n Como Real\n\n    Escribir \"Ingrese un numero:\"\n\n    Leer n\n\n    Si n > 0 Entonces\n\n        Escribir \"Es positivo\"\n\n    SiNo\n\n        Si n < 0 Entonces\n\n            Escribir \"Es negativo\"\n\n        SiNo\n\n            Escribir \"Es cero\"\n\n        FinSi\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 22,
        "titulo": "Par o impar",
        "enunciado": "Pedir un número entero y decir si es par o impar.",
        "solucion": "Proceso Ejercicio22\n\n    Definir n Como Entero\n\n    Escribir \"Ingrese un numero:\"\n\n    Leer n\n\n    Si n MOD 2 = 0 Entonces\n\n        Escribir \"Es par\"\n\n    SiNo\n\n        Escribir \"Es impar\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 23,
        "titulo": "Mayor de edad",
        "enunciado": "Pedir la edad y decir si la persona es mayor de edad.",
        "solucion": "Proceso Ejercicio23\n\n    Definir edad Como Entero\n\n    Escribir \"Ingrese su edad:\"\n\n    Leer edad\n\n    Si edad >= 18 Entonces\n\n        Escribir \"Mayor de edad\"\n\n    SiNo\n\n        Escribir \"Menor de edad\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 24,
        "titulo": "Aprobado o reprobado",
        "enunciado": "Pedir una nota y decir si aprueba con 4.0 o más.",
        "solucion": "Proceso Ejercicio24\n\n    Definir nota Como Real\n\n    Escribir \"Ingrese la nota:\"\n\n    Leer nota\n\n    Si nota >= 4.0 Entonces\n\n        Escribir \"Aprobado\"\n\n    SiNo\n\n        Escribir \"Reprobado\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 25,
        "titulo": "Mayor entre dos números",
        "enunciado": "Pedir dos números y mostrar el mayor.",
        "solucion": "Proceso Ejercicio25\n\n    Definir a, b Como Real\n\n    Escribir \"Ingrese el primer numero:\"\n\n    Leer a\n\n    Escribir \"Ingrese el segundo numero:\"\n\n    Leer b\n\n    Si a > b Entonces\n\n        Escribir \"El mayor es: \", a\n\n    SiNo\n\n        Si b > a Entonces\n\n            Escribir \"El mayor es: \", b\n\n        SiNo\n\n            Escribir \"Son iguales\"\n\n        FinSi\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 26,
        "titulo": "Menor entre tres números",
        "enunciado": "Pedir tres números y mostrar el menor.",
        "solucion": "Proceso Ejercicio26\n\n    Definir a, b, c, menor Como Real\n\n    Escribir \"Ingrese el primer numero:\"\n\n    Leer a\n\n    Escribir \"Ingrese el segundo numero:\"\n\n    Leer b\n\n    Escribir \"Ingrese el tercer numero:\"\n\n    Leer c\n\n    menor <- a\n\n    Si b < menor Entonces\n\n        menor <- b\n\n    FinSi\n\n    Si c < menor Entonces\n\n        menor <- c\n\n    FinSi\n\n    Escribir \"El menor es: \", menor\n\nFinProceso"
    },
    {
        "numero": 27,
        "titulo": "Número dentro de rango",
        "enunciado": "Pedir un número y decir si está entre 10 y 20 inclusive.",
        "solucion": "Proceso Ejercicio27\n\n    Definir n Como Entero\n\n    Escribir \"Ingrese un numero:\"\n\n    Leer n\n\n    Si n >= 10 Y n <= 20 Entonces\n\n        Escribir \"Esta dentro del rango\"\n\n    SiNo\n\n        Escribir \"Esta fuera del rango\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 28,
        "titulo": "Múltiplo de 5",
        "enunciado": "Pedir un número y decir si es múltiplo de 5.",
        "solucion": "Proceso Ejercicio28\n\n    Definir n Como Entero\n\n    Escribir \"Ingrese un numero:\"\n\n    Leer n\n\n    Si n MOD 5 = 0 Entonces\n\n        Escribir \"Es multiplo de 5\"\n\n    SiNo\n\n        Escribir \"No es multiplo de 5\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 29,
        "titulo": "Año bisiesto",
        "enunciado": "Pedir un año y decir si es bisiesto.",
        "solucion": "Proceso Ejercicio29\n\n    Definir anio Como Entero\n\n    Escribir \"Ingrese un anio:\"\n\n    Leer anio\n\n    Si (anio MOD 4 = 0 Y anio MOD 100 <> 0) O (anio MOD 400 = 0) Entonces\n\n        Escribir \"Es bisiesto\"\n\n    SiNo\n\n        Escribir \"No es bisiesto\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 30,
        "titulo": "Comparar dos cadenas",
        "enunciado": "Pedir dos palabras y decir si son iguales.",
        "solucion": "Proceso Ejercicio30\n\n    Definir palabra1, palabra2 Como Cadena\n\n    Escribir \"Ingrese la primera palabra:\"\n\n    Leer palabra1\n\n    Escribir \"Ingrese la segunda palabra:\"\n\n    Leer palabra2\n\n    Si palabra1 = palabra2 Entonces\n\n        Escribir \"Son iguales\"\n\n    SiNo\n\n        Escribir \"Son diferentes\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 31,
        "titulo": "Precio con envío",
        "enunciado": "Pedir el monto de compra. Si supera 50000, el envío es gratis; si no, sumar 3000.",
        "solucion": "Proceso Ejercicio31\n\n    Definir compra, total Como Real\n\n    Escribir \"Ingrese el monto de compra:\"\n\n    Leer compra\n\n    Si compra > 50000 Entonces\n\n        total <- compra\n\n    SiNo\n\n        total <- compra + 3000\n\n    FinSi\n\n    Escribir \"Total a pagar: \", total\n\nFinProceso"
    },
    {
        "numero": 32,
        "titulo": "Clave correcta",
        "enunciado": "Pedir una clave y decir si coincide con \"1234\".",
        "solucion": "Proceso Ejercicio32\n\n    Definir clave Como Cadena\n\n    Escribir \"Ingrese la clave:\"\n\n    Leer clave\n\n    Si clave = \"1234\" Entonces\n\n        Escribir \"Clave correcta\"\n\n    SiNo\n\n        Escribir \"Clave incorrecta\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 33,
        "titulo": "Descuento por edad",
        "enunciado": "Si la persona tiene 60 años o más, obtiene 25% de descuento. Pedir edad y precio.",
        "solucion": "Proceso Ejercicio33\n\n    Definir edad Como Entero\n\n    Definir precio, total Como Real\n\n    Escribir \"Ingrese edad:\"\n\n    Leer edad\n\n    Escribir \"Ingrese precio:\"\n\n    Leer precio\n\n    Si edad >= 60 Entonces\n\n        total <- precio - (precio * 0.25)\n\n    SiNo\n\n        total <- precio\n\n    FinSi\n\n    Escribir \"Total a pagar: \", total\n\nFinProceso"
    },
    {
        "numero": 34,
        "titulo": "Ordenar dos números",
        "enunciado": "Pedir dos números y mostrarlos en orden ascendente.",
        "solucion": "Proceso Ejercicio34\n\n    Definir a, b Como Real\n\n    Escribir \"Ingrese el primer numero:\"\n\n    Leer a\n\n    Escribir \"Ingrese el segundo numero:\"\n\n    Leer b\n\n    Si a < b Entonces\n\n        Escribir a, \" \", b\n\n    SiNo\n\n        Escribir b, \" \", a\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 35,
        "titulo": "Calificación literal",
        "enunciado": "Pedir una nota y mostrar Excelente si es 7, Muy bien si es mayor o igual a 6, Bien si es mayor o igual a 5, y Reprobado si es menor a 4.",
        "solucion": "Proceso Ejercicio35\n\n    Definir nota Como Real\n\n    Escribir \"Ingrese la nota:\"\n\n    Leer nota\n\n    Si nota = 7 Entonces\n\n        Escribir \"Excelente\"\n\n    SiNo\n\n        Si nota >= 6 Entonces\n\n            Escribir \"Muy bien\"\n\n        SiNo\n\n            Si nota >= 5 Entonces\n\n                Escribir \"Bien\"\n\n            SiNo\n\n                Si nota >= 4 Entonces\n\n                    Escribir \"Suficiente\"\n\n                SiNo\n\n                    Escribir \"Reprobado\"\n\n                FinSi\n\n            FinSi\n\n        FinSi\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 36,
        "titulo": "Puede entrar al juego",
        "enunciado": "Pedir edad y si viene acompañado por un adulto (SI/NO). Puede entrar si tiene 18 o más, o si viene acompañado.",
        "solucion": "Proceso Ejercicio36\n\n    Definir edad Como Entero\n\n    Definir acomp Como Cadena\n\n    Escribir \"Ingrese edad:\"\n\n    Leer edad\n\n    Escribir \"Viene acompanado? (SI/NO):\"\n\n    Leer acomp\n\n    acomp <- Mayusculas(acomp)\n\n    Si edad >= 18 O acomp = \"SI\" Entonces\n\n        Escribir \"Puede entrar\"\n\n    SiNo\n\n        Escribir \"No puede entrar\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 37,
        "titulo": "Número de una cifra, dos cifras o más",
        "enunciado": "Pedir un número entero positivo y decir si tiene una cifra, dos cifras o más.",
        "solucion": "Proceso Ejercicio37\n\n    Definir n Como Entero\n\n    Escribir \"Ingrese un numero entero positivo:\"\n\n    Leer n\n\n    Si n < 10 Entonces\n\n        Escribir \"Tiene una cifra\"\n\n    SiNo\n\n        Si n < 100 Entonces\n\n            Escribir \"Tiene dos cifras\"\n\n        SiNo\n\n            Escribir \"Tiene tres o mas cifras\"\n\n        FinSi\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 38,
        "titulo": "Triángulo válido",
        "enunciado": "Pedir tres lados y decir si pueden formar un triángulo.",
        "solucion": "Proceso Ejercicio38\n\n    Definir a, b, c Como Real\n\n    Escribir \"Ingrese lado 1:\"\n\n    Leer a\n\n    Escribir \"Ingrese lado 2:\"\n\n    Leer b\n\n    Escribir \"Ingrese lado 3:\"\n\n    Leer c\n\n    Si a + b > c Y a + c > b Y b + c > a Entonces\n\n        Escribir \"Forman un triangulo\"\n\n    SiNo\n\n        Escribir \"No forman un triangulo\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 39,
        "titulo": "Tipo de triángulo",
        "enunciado": "Pedir tres lados y decir si el triángulo es equilátero, isósceles o escaleno.",
        "solucion": "Proceso Ejercicio39\n\n    Definir a, b, c Como Real\n\n    Escribir \"Ingrese lado 1:\"\n\n    Leer a\n\n    Escribir \"Ingrese lado 2:\"\n\n    Leer b\n\n    Escribir \"Ingrese lado 3:\"\n\n    Leer c\n\n    Si a = b Y b = c Entonces\n\n        Escribir \"Equilatero\"\n\n    SiNo\n\n        Si a = b O a = c O b = c Entonces\n\n            Escribir \"Isosceles\"\n\n        SiNo\n\n            Escribir \"Escaleno\"\n\n        FinSi\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 40,
        "titulo": "Valor absoluto",
        "enunciado": "Pedir un número y mostrar su valor absoluto sin usar Abs.",
        "solucion": "Proceso Ejercicio40\n\n    Definir n, valorAbs Como Real\n\n    Escribir \"Ingrese un numero:\"\n\n    Leer n\n\n    Si n < 0 Entonces\n\n        valorAbs <- n * -1\n\n    SiNo\n\n        valorAbs <- n\n\n    FinSi\n\n    Escribir \"Valor absoluto: \", valorAbs\n\nFinProceso"
    },
    {
        "numero": 41,
        "titulo": "Día de la semana con SEGUN",
        "enunciado": "Pedir un número del 1 al 7 y mostrar el día correspondiente.",
        "solucion": "Proceso Ejercicio41\n\n    Definir dia Como Entero\n\n    Escribir \"Ingrese un numero del 1 al 7:\"\n\n    Leer dia\n\n    Segun dia Hacer\n\n        1:\n\n            Escribir \"Lunes\"\n\n        2:\n\n            Escribir \"Martes\"\n\n        3:\n\n            Escribir \"Miercoles\"\n\n        4:\n\n            Escribir \"Jueves\"\n\n        5:\n\n            Escribir \"Viernes\"\n\n        6:\n\n            Escribir \"Sabado\"\n\n        7:\n\n            Escribir \"Domingo\"\n\n        De Otro Modo:\n\n            Escribir \"Numero invalido\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 42,
        "titulo": "Mes del año con SEGUN",
        "enunciado": "Pedir un número del 1 al 12 y mostrar el mes.",
        "solucion": "Proceso Ejercicio42\n\n    Definir mes Como Entero\n\n    Escribir \"Ingrese un numero del 1 al 12:\"\n\n    Leer mes\n\n    Segun mes Hacer\n\n        1: Escribir \"Enero\"\n\n        2: Escribir \"Febrero\"\n\n        3: Escribir \"Marzo\"\n\n        4: Escribir \"Abril\"\n\n        5: Escribir \"Mayo\"\n\n        6: Escribir \"Junio\"\n\n        7: Escribir \"Julio\"\n\n        8: Escribir \"Agosto\"\n\n        9: Escribir \"Septiembre\"\n\n        10: Escribir \"Octubre\"\n\n        11: Escribir \"Noviembre\"\n\n        12: Escribir \"Diciembre\"\n\n        De Otro Modo:\n\n            Escribir \"Mes invalido\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 43,
        "titulo": "Menú de operaciones",
        "enunciado": "Pedir dos números y una opción: 1 sumar, 2 restar, 3 multiplicar, 4 dividir.",
        "solucion": "Proceso Ejercicio43\n\n    Definir a, b, resultado Como Real\n\n    Definir opcion Como Entero\n\n    Escribir \"Ingrese el primer numero:\"\n\n    Leer a\n\n    Escribir \"Ingrese el segundo numero:\"\n\n    Leer b\n\n    Escribir \"1. Sumar\"\n\n    Escribir \"2. Restar\"\n\n    Escribir \"3. Multiplicar\"\n\n    Escribir \"4. Dividir\"\n\n    Leer opcion\n\n    Segun opcion Hacer\n\n        1:\n\n            resultado <- a + b\n\n            Escribir \"Resultado: \", resultado\n\n        2:\n\n            resultado <- a - b\n\n            Escribir \"Resultado: \", resultado\n\n        3:\n\n            resultado <- a * b\n\n            Escribir \"Resultado: \", resultado\n\n        4:\n\n            resultado <- a / b\n\n            Escribir \"Resultado: \", resultado\n\n        De Otro Modo:\n\n            Escribir \"Opcion invalida\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 44,
        "titulo": "Tipo de vocal",
        "enunciado": "Pedir una letra y decir si es vocal.",
        "solucion": "Proceso Ejercicio44\n\n    Definir letra Como Cadena\n\n    Escribir \"Ingrese una letra:\"\n\n    Leer letra\n\n    letra <- Mayusculas(letra)\n\n    Segun letra Hacer\n\n        \"A\", \"E\", \"I\", \"O\", \"U\":\n\n            Escribir \"Es vocal\"\n\n        De Otro Modo:\n\n            Escribir \"No es vocal\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 45,
        "titulo": "Cantidad de días del mes",
        "enunciado": "Pedir un número de mes y mostrar cuántos días tiene. Febrero contará como 28.",
        "solucion": "Proceso Ejercicio45\n\n    Definir mes Como Entero\n\n    Escribir \"Ingrese el numero del mes:\"\n\n    Leer mes\n\n    Segun mes Hacer\n\n        1, 3, 5, 7, 8, 10, 12:\n\n            Escribir \"Tiene 31 dias\"\n\n        4, 6, 9, 11:\n\n            Escribir \"Tiene 30 dias\"\n\n        2:\n\n            Escribir \"Tiene 28 dias\"\n\n        De Otro Modo:\n\n            Escribir \"Mes invalido\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 46,
        "titulo": "Conversión de unidades",
        "enunciado": "Pedir una opción: 1 metros a cm, 2 kg a gramos, 3 horas a minutos.",
        "solucion": "Proceso Ejercicio46\n\n    Definir opcion Como Entero\n\n    Definir valor Como Real\n\n    Escribir \"1. Metros a centimetros\"\n\n    Escribir \"2. Kilos a gramos\"\n\n    Escribir \"3. Horas a minutos\"\n\n    Leer opcion\n\n    Escribir \"Ingrese el valor:\"\n\n    Leer valor\n\n    Segun opcion Hacer\n\n        1:\n\n            Escribir \"Resultado: \", valor * 100\n\n        2:\n\n            Escribir \"Resultado: \", valor * 1000\n\n        3:\n\n            Escribir \"Resultado: \", valor * 60\n\n        De Otro Modo:\n\n            Escribir \"Opcion invalida\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 47,
        "titulo": "Turno del día",
        "enunciado": "Pedir una hora del día de 0 a 23 y mostrar madrugada, mañana, tarde o noche usando SEGUN con rangos.",
        "solucion": "Proceso Ejercicio47\n\n    Definir hora Como Entero\n\n    Escribir \"Ingrese una hora de 0 a 23:\"\n\n    Leer hora\n\n    Segun hora Hacer\n\n        0, 1, 2, 3, 4, 5:\n\n            Escribir \"Madrugada\"\n\n        6, 7, 8, 9, 10, 11:\n\n            Escribir \"Manana\"\n\n        12, 13, 14, 15, 16, 17:\n\n            Escribir \"Tarde\"\n\n        18, 19, 20, 21, 22, 23:\n\n            Escribir \"Noche\"\n\n        De Otro Modo:\n\n            Escribir \"Hora invalida\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 48,
        "titulo": "Menú de bebidas",
        "enunciado": "Pedir una opción de bebida y mostrar su precio.",
        "solucion": "Proceso Ejercicio48\n\n    Definir opcion Como Entero\n\n    Escribir \"1. Agua\"\n\n    Escribir \"2. Jugo\"\n\n    Escribir \"3. Bebida\"\n\n    Escribir \"4. Cafe\"\n\n    Leer opcion\n\n    Segun opcion Hacer\n\n        1: Escribir \"Precio: 1000\"\n\n        2: Escribir \"Precio: 1500\"\n\n        3: Escribir \"Precio: 1800\"\n\n        4: Escribir \"Precio: 1200\"\n\n        De Otro Modo:\n\n            Escribir \"Opcion invalida\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 49,
        "titulo": "Notas por concepto",
        "enunciado": "Pedir una letra A, B, C, D o F y mostrar el concepto asociado.",
        "solucion": "Proceso Ejercicio49\n\n    Definir letra Como Cadena\n\n    Escribir \"Ingrese una letra (A, B, C, D, F):\"\n\n    Leer letra\n\n    letra <- Mayusculas(letra)\n\n    Segun letra Hacer\n\n        \"A\":\n\n            Escribir \"Excelente\"\n\n        \"B\":\n\n            Escribir \"Muy bien\"\n\n        \"C\":\n\n            Escribir \"Bien\"\n\n        \"D\":\n\n            Escribir \"Regular\"\n\n        \"F\":\n\n            Escribir \"Insuficiente\"\n\n        De Otro Modo:\n\n            Escribir \"Letra invalida\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 50,
        "titulo": "Calculadora con símbolo",
        "enunciado": "Pedir dos números y un operador (+, -, *, /) y resolver con SEGUN.",
        "solucion": "Proceso Ejercicio50\n\n    Definir a, b Como Real\n\n    Definir op Como Cadena\n\n    Escribir \"Ingrese el primer numero:\"\n\n    Leer a\n\n    Escribir \"Ingrese el segundo numero:\"\n\n    Leer b\n\n    Escribir \"Ingrese operador (+, -, *, /):\"\n\n    Leer op\n\n    Segun op Hacer\n\n        \"+\":\n\n            Escribir \"Resultado: \", a + b\n\n        \"-\":\n\n            Escribir \"Resultado: \", a - b\n\n        \"*\":\n\n            Escribir \"Resultado: \", a * b\n\n        \"/\":\n\n            Escribir \"Resultado: \", a / b\n\n        De Otro Modo:\n\n            Escribir \"Operador invalido\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 51,
        "titulo": "Opción de menú principal",
        "enunciado": "Crear un menú con 1 Iniciar, 2 Configuración, 3 Salir.",
        "solucion": "Proceso Ejercicio51\n\n    Definir opcion Como Entero\n\n    Escribir \"1. Iniciar\"\n\n    Escribir \"2. Configuracion\"\n\n    Escribir \"3. Salir\"\n\n    Leer opcion\n\n    Segun opcion Hacer\n\n        1:\n\n            Escribir \"Iniciando...\"\n\n        2:\n\n            Escribir \"Abriendo configuracion...\"\n\n        3:\n\n            Escribir \"Saliendo...\"\n\n        De Otro Modo:\n\n            Escribir \"Opcion invalida\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 52,
        "titulo": "Tarifa de transporte",
        "enunciado": "Pedir tipo de pasajero: 1 niño, 2 adulto, 3 adulto mayor. Mostrar tarifa.",
        "solucion": "Proceso Ejercicio52\n\n    Definir tipo Como Entero\n\n    Escribir \"1. Nino\"\n\n    Escribir \"2. Adulto\"\n\n    Escribir \"3. Adulto mayor\"\n\n    Leer tipo\n\n    Segun tipo Hacer\n\n        1:\n\n            Escribir \"Tarifa: 300\"\n\n        2:\n\n            Escribir \"Tarifa: 700\"\n\n        3:\n\n            Escribir \"Tarifa: 350\"\n\n        De Otro Modo:\n\n            Escribir \"Tipo invalido\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 53,
        "titulo": "Convertir número a palabra",
        "enunciado": "Pedir un número del 1 al 5 y escribirlo en palabras.",
        "solucion": "Proceso Ejercicio53\n\n    Definir n Como Entero\n\n    Escribir \"Ingrese un numero del 1 al 5:\"\n\n    Leer n\n\n    Segun n Hacer\n\n        1: Escribir \"Uno\"\n\n        2: Escribir \"Dos\"\n\n        3: Escribir \"Tres\"\n\n        4: Escribir \"Cuatro\"\n\n        5: Escribir \"Cinco\"\n\n        De Otro Modo:\n\n            Escribir \"Numero invalido\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 54,
        "titulo": "Estación del año",
        "enunciado": "Pedir un número del 1 al 4 y mostrar la estación del año.",
        "solucion": "Proceso Ejercicio54\n\n    Definir opcion Como Entero\n\n    Escribir \"1. Verano\"\n\n    Escribir \"2. Otono\"\n\n    Escribir \"3. Invierno\"\n\n    Escribir \"4. Primavera\"\n\n    Leer opcion\n\n    Segun opcion Hacer\n\n        1: Escribir \"Verano\"\n\n        2: Escribir \"Otono\"\n\n        3: Escribir \"Invierno\"\n\n        4: Escribir \"Primavera\"\n\n        De Otro Modo:\n\n            Escribir \"Opcion invalida\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 55,
        "titulo": "Nivel de dificultad",
        "enunciado": "Pedir una opción de 1 a 3 y mostrar Fácil, Medio o Difícil.",
        "solucion": "Proceso Ejercicio55\n\n    Definir nivel Como Entero\n\n    Escribir \"Ingrese nivel (1 a 3):\"\n\n    Leer nivel\n\n    Segun nivel Hacer\n\n        1:\n\n            Escribir \"Facil\"\n\n        2:\n\n            Escribir \"Medio\"\n\n        3:\n\n            Escribir \"Dificil\"\n\n        De Otro Modo:\n\n            Escribir \"Nivel invalido\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 56,
        "titulo": "Contar del 1 al 10",
        "enunciado": "Mostrar los números del 1 al 10 usando PARA.",
        "solucion": "Proceso Ejercicio56\n\n    Definir i Como Entero\n\n    Para i <- 1 Hasta 10 Hacer\n\n        Escribir i\n\n    FinPara\n\nFinProceso"
    },
    {
        "numero": 57,
        "titulo": "Contar del 10 al 1",
        "enunciado": "Mostrar los números del 10 al 1 usando PARA.",
        "solucion": "Proceso Ejercicio57\n\n    Definir i Como Entero\n\n    Para i <- 10 Hasta 1 Con Paso -1 Hacer\n\n        Escribir i\n\n    FinPara\n\nFinProceso"
    },
    {
        "numero": 58,
        "titulo": "Tabla de multiplicar",
        "enunciado": "Pedir un número y mostrar su tabla del 1 al 10.",
        "solucion": "Proceso Ejercicio58\n\n    Definir n, i Como Entero\n\n    Escribir \"Ingrese un numero:\"\n\n    Leer n\n\n    Para i <- 1 Hasta 10 Hacer\n\n        Escribir n, \" x \", i, \" = \", n * i\n\n    FinPara\n\nFinProceso"
    },
    {
        "numero": 59,
        "titulo": "Suma del 1 al 100",
        "enunciado": "Calcular la suma de los números del 1 al 100.",
        "solucion": "Proceso Ejercicio59\n\n    Definir i, suma Como Entero\n\n    suma <- 0\n\n    Para i <- 1 Hasta 100 Hacer\n\n        suma <- suma + i\n\n    FinPara\n\n    Escribir \"La suma es: \", suma\n\nFinProceso"
    },
    {
        "numero": 60,
        "titulo": "Sumar 5 números",
        "enunciado": "Pedir 5 números y mostrar la suma total.",
        "solucion": "Proceso Ejercicio60\n\n    Definir i Como Entero\n\n    Definir n, suma Como Real\n\n    suma <- 0\n\n    Para i <- 1 Hasta 5 Hacer\n\n        Escribir \"Ingrese un numero:\"\n\n        Leer n\n\n        suma <- suma + n\n\n    FinPara\n\n    Escribir \"Suma total: \", suma\n\nFinProceso"
    },
    {
        "numero": 61,
        "titulo": "Promedio de 5 números",
        "enunciado": "Pedir 5 números y mostrar el promedio.",
        "solucion": "Proceso Ejercicio61\n\n    Definir i Como Entero\n\n    Definir n, suma, promedio Como Real\n\n    suma <- 0\n\n    Para i <- 1 Hasta 5 Hacer\n\n        Escribir \"Ingrese un numero:\"\n\n        Leer n\n\n        suma <- suma + n\n\n    FinPara\n\n    promedio <- suma / 5\n\n    Escribir \"Promedio: \", promedio\n\nFinProceso"
    },
    {
        "numero": 62,
        "titulo": "Contar positivos",
        "enunciado": "Pedir 10 números y contar cuántos son positivos.",
        "solucion": "Proceso Ejercicio62\n\n    Definir i, n, contador Como Entero\n\n    contador <- 0\n\n    Para i <- 1 Hasta 10 Hacer\n\n        Escribir \"Ingrese un numero:\"\n\n        Leer n\n\n        Si n > 0 Entonces\n\n            contador <- contador + 1\n\n        FinSi\n\n    FinPara\n\n    Escribir \"Cantidad de positivos: \", contador\n\nFinProceso"
    },
    {
        "numero": 63,
        "titulo": "Contar pares",
        "enunciado": "Pedir 10 números y contar cuántos son pares.",
        "solucion": "Proceso Ejercicio63\n\n    Definir i, n, contador Como Entero\n\n    contador <- 0\n\n    Para i <- 1 Hasta 10 Hacer\n\n        Escribir \"Ingrese un numero:\"\n\n        Leer n\n\n        Si n MOD 2 = 0 Entonces\n\n            contador <- contador + 1\n\n        FinSi\n\n    FinPara\n\n    Escribir \"Cantidad de pares: \", contador\n\nFinProceso"
    },
    {
        "numero": 64,
        "titulo": "Mayor ingresado",
        "enunciado": "Pedir 5 números y mostrar el mayor.",
        "solucion": "Proceso Ejercicio64\n\n    Definir i Como Entero\n\n    Definir n, mayor Como Real\n\n    Para i <- 1 Hasta 5 Hacer\n\n        Escribir \"Ingrese un numero:\"\n\n        Leer n\n\n        Si i = 1 O n > mayor Entonces\n\n            mayor <- n\n\n        FinSi\n\n    FinPara\n\n    Escribir \"El mayor es: \", mayor\n\nFinProceso"
    },
    {
        "numero": 65,
        "titulo": "Menor ingresado",
        "enunciado": "Pedir 5 números y mostrar el menor.",
        "solucion": "Proceso Ejercicio65\n\n    Definir i Como Entero\n\n    Definir n, menor Como Real\n\n    Para i <- 1 Hasta 5 Hacer\n\n        Escribir \"Ingrese un numero:\"\n\n        Leer n\n\n        Si i = 1 O n < menor Entonces\n\n            menor <- n\n\n        FinSi\n\n    FinPara\n\n    Escribir \"El menor es: \", menor\n\nFinProceso"
    },
    {
        "numero": 66,
        "titulo": "Factorial de un número",
        "enunciado": "Pedir un número y calcular su factorial.",
        "solucion": "Proceso Ejercicio66\n\n    Definir n, i, factorial Como Entero\n\n    Escribir \"Ingrese un numero:\"\n\n    Leer n\n\n    factorial <- 1\n\n    Para i <- 1 Hasta n Hacer\n\n        factorial <- factorial * i\n\n    FinPara\n\n    Escribir \"Factorial: \", factorial\n\nFinProceso"
    },
    {
        "numero": 67,
        "titulo": "Potencia por multiplicación",
        "enunciado": "Pedir base y exponente entero positivo, y calcular la potencia sin usar ^.",
        "solucion": "Proceso Ejercicio67\n\n    Definir base, resultado Como Real\n\n    Definir exponente, i Como Entero\n\n    Escribir \"Ingrese la base:\"\n\n    Leer base\n\n    Escribir \"Ingrese el exponente:\"\n\n    Leer exponente\n\n    resultado <- 1\n\n    Para i <- 1 Hasta exponente Hacer\n\n        resultado <- resultado * base\n\n    FinPara\n\n    Escribir \"Resultado: \", resultado\n\nFinProceso"
    },
    {
        "numero": 68,
        "titulo": "Contar hasta N",
        "enunciado": "Pedir un número N y mostrar del 1 hasta N usando MIENTRAS.",
        "solucion": "Proceso Ejercicio68\n\n    Definir n, i Como Entero\n\n    Escribir \"Ingrese N:\"\n\n    Leer n\n\n    i <- 1\n\n    Mientras i <= n Hacer\n\n        Escribir i\n\n        i <- i + 1\n\n    FinMientras\n\nFinProceso"
    },
    {
        "numero": 69,
        "titulo": "Contar de N a 1",
        "enunciado": "Pedir un número N y mostrar desde N hasta 1 usando MIENTRAS.",
        "solucion": "Proceso Ejercicio69\n\n    Definir n Como Entero\n\n    Escribir \"Ingrese N:\"\n\n    Leer n\n\n    Mientras n >= 1 Hacer\n\n        Escribir n\n\n        n <- n - 1\n\n    FinMientras\n\nFinProceso"
    },
    {
        "numero": 70,
        "titulo": "Validar contraseña",
        "enunciado": "Pedir una contraseña hasta que el usuario escriba \"1234\".",
        "solucion": "Proceso Ejercicio70\n\n    Definir clave Como Cadena\n\n    clave <- \"\"\n\n    Mientras clave <> \"1234\" Hacer\n\n        Escribir \"Ingrese la clave:\"\n\n        Leer clave\n\n    FinMientras\n\n    Escribir \"Clave correcta\"\n\nFinProceso"
    },
    {
        "numero": 71,
        "titulo": "Pedir número positivo",
        "enunciado": "Seguir pidiendo un número hasta que sea positivo.",
        "solucion": "Proceso Ejercicio71\n\n    Definir n Como Real\n\n    n <- -1\n\n    Mientras n <= 0 Hacer\n\n        Escribir \"Ingrese un numero positivo:\"\n\n        Leer n\n\n    FinMientras\n\n    Escribir \"Numero valido: \", n\n\nFinProceso"
    },
    {
        "numero": 72,
        "titulo": "Suma hasta que ingrese 0",
        "enunciado": "Pedir números y sumarlos hasta que el usuario ingrese 0.",
        "solucion": "Proceso Ejercicio72\n\n    Definir n, suma Como Real\n\n    suma <- 0\n\n    Escribir \"Ingrese un numero (0 para terminar):\"\n\n    Leer n\n\n    Mientras n <> 0 Hacer\n\n        suma <- suma + n\n\n        Escribir \"Ingrese un numero (0 para terminar):\"\n\n        Leer n\n\n    FinMientras\n\n    Escribir \"Suma total: \", suma\n\nFinProceso"
    },
    {
        "numero": 73,
        "titulo": "Promedio hasta centinela",
        "enunciado": "Pedir números hasta ingresar 0. Mostrar promedio de los números distintos de 0.",
        "solucion": "Proceso Ejercicio73\n\n    Definir n, suma, promedio Como Real\n\n    Definir contador Como Entero\n\n    suma <- 0\n\n    contador <- 0\n\n    Escribir \"Ingrese un numero (0 para terminar):\"\n\n    Leer n\n\n    Mientras n <> 0 Hacer\n\n        suma <- suma + n\n\n        contador <- contador + 1\n\n        Escribir \"Ingrese un numero (0 para terminar):\"\n\n        Leer n\n\n    FinMientras\n\n    Si contador > 0 Entonces\n\n        promedio <- suma / contador\n\n        Escribir \"Promedio: \", promedio\n\n    SiNo\n\n        Escribir \"No se ingresaron numeros\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 74,
        "titulo": "Contar vocales en 5 letras",
        "enunciado": "Pedir 5 letras y contar cuántas son vocales.",
        "solucion": "Proceso Ejercicio74\n\n    Definir i, contador Como Entero\n\n    Definir letra Como Cadena\n\n    contador <- 0\n\n    Para i <- 1 Hasta 5 Hacer\n\n        Escribir \"Ingrese una letra:\"\n\n        Leer letra\n\n        letra <- Mayusculas(letra)\n\n        Si letra = \"A\" O letra = \"E\" O letra = \"I\" O letra = \"O\" O letra = \"U\" Entonces\n\n            contador <- contador + 1\n\n        FinSi\n\n    FinPara\n\n    Escribir \"Cantidad de vocales: \", contador\n\nFinProceso"
    },
    {
        "numero": 75,
        "titulo": "Repetir hasta nota válida",
        "enunciado": "Pedir una nota hasta que esté entre 1.0 y 7.0.",
        "solucion": "Proceso Ejercicio75\n\n    Definir nota Como Real\n\n    Repetir\n\n        Escribir \"Ingrese una nota entre 1.0 y 7.0:\"\n\n        Leer nota\n\n    Hasta Que nota >= 1 Y nota <= 7\n\n    Escribir \"Nota valida: \", nota\n\nFinProceso"
    },
    {
        "numero": 76,
        "titulo": "Menú repetitivo",
        "enunciado": "Mostrar un menú hasta que el usuario elija salir.",
        "solucion": "Proceso Ejercicio76\n\n    Definir opcion Como Entero\n\n    Repetir\n\n        Escribir \"1. Saludar\"\n\n        Escribir \"2. Mostrar fecha ficticia\"\n\n        Escribir \"3. Salir\"\n\n        Leer opcion\n\n        Segun opcion Hacer\n\n            1:\n\n                Escribir \"Hola\"\n\n            2:\n\n                Escribir \"Fecha ficticia: 01/01/2026\"\n\n            3:\n\n                Escribir \"Saliendo...\"\n\n            De Otro Modo:\n\n                Escribir \"Opcion invalida\"\n\n        FinSegun\n\n    Hasta Que opcion = 3\n\nFinProceso"
    },
    {
        "numero": 77,
        "titulo": "Adivinar hasta acertar",
        "enunciado": "Pedir un número hasta que el usuario escriba 7.",
        "solucion": "Proceso Ejercicio77\n\n    Definir n Como Entero\n\n    Repetir\n\n        Escribir \"Adivina el numero:\"\n\n        Leer n\n\n    Hasta Que n = 7\n\n    Escribir \"Acertaste\"\n\nFinProceso"
    },
    {
        "numero": 78,
        "titulo": "Mostrar pares hasta N",
        "enunciado": "Pedir un número N y mostrar los números pares desde 2 hasta N.",
        "solucion": "Proceso Ejercicio78\n\n    Definir n, i Como Entero\n\n    Escribir \"Ingrese N:\"\n\n    Leer n\n\n    Para i <- 2 Hasta n Con Paso 2 Hacer\n\n        Escribir i\n\n    FinPara\n\nFinProceso"
    },
    {
        "numero": 79,
        "titulo": "Multiplicar acumulando",
        "enunciado": "Pedir 4 números y mostrar el producto total.",
        "solucion": "Proceso Ejercicio79\n\n    Definir i Como Entero\n\n    Definir n, producto Como Real\n\n    producto <- 1\n\n    Para i <- 1 Hasta 4 Hacer\n\n        Escribir \"Ingrese un numero:\"\n\n        Leer n\n\n        producto <- producto * n\n\n    FinPara\n\n    Escribir \"Producto total: \", producto\n\nFinProceso"
    },
    {
        "numero": 80,
        "titulo": "Serie de cuadrados",
        "enunciado": "Mostrar el cuadrado de los números del 1 al 10.",
        "solucion": "Proceso Ejercicio80\n\n    Definir i Como Entero\n\n    Para i <- 1 Hasta 10 Hacer\n\n        Escribir \"El cuadrado de \", i, \" es \", i * i\n\n    FinPara\n\nFinProceso"
    },
    {
        "numero": 81,
        "titulo": "Número aleatorio del 1 al 10",
        "enunciado": "Generar y mostrar un número aleatorio entre 1 y 10.",
        "solucion": "Proceso Ejercicio81\n\n    Definir n Como Entero\n\n    n <- Aleatorio(1, 10)\n\n    Escribir \"Numero aleatorio: \", n\n\nFinProceso"
    },
    {
        "numero": 82,
        "titulo": "Moneda al aire",
        "enunciado": "Simular una moneda: 1 cara, 2 sello.",
        "solucion": "Proceso Ejercicio82\n\n    Definir moneda Como Entero\n\n    moneda <- Aleatorio(1, 2)\n\n    Si moneda = 1 Entonces\n\n        Escribir \"Cara\"\n\n    SiNo\n\n        Escribir \"Sello\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 83,
        "titulo": "Dado de 6 caras",
        "enunciado": "Simular el lanzamiento de un dado.",
        "solucion": "Proceso Ejercicio83\n\n    Definir dado Como Entero\n\n    dado <- Aleatorio(1, 6)\n\n    Escribir \"Salio: \", dado\n\nFinProceso"
    },
    {
        "numero": 84,
        "titulo": "Dos dados y suma",
        "enunciado": "Lanzar dos dados aleatorios y mostrar su suma.",
        "solucion": "Proceso Ejercicio84\n\n    Definir dado1, dado2, suma Como Entero\n\n    dado1 <- Aleatorio(1, 6)\n\n    dado2 <- Aleatorio(1, 6)\n\n    suma <- dado1 + dado2\n\n    Escribir \"Dado 1: \", dado1\n\n    Escribir \"Dado 2: \", dado2\n\n    Escribir \"Suma: \", suma\n\nFinProceso"
    },
    {
        "numero": 85,
        "titulo": "Adivina el número aleatorio",
        "enunciado": "Generar un número aleatorio entre 1 y 10 y pedir intentos hasta acertar.",
        "solucion": "Proceso Ejercicio85\n\n    Definir secreto, intento Como Entero\n\n    secreto <- Aleatorio(1, 10)\n\n    Repetir\n\n        Escribir \"Adivine el numero entre 1 y 10:\"\n\n        Leer intento\n\n    Hasta Que intento = secreto\n\n    Escribir \"Acertaste\"\n\nFinProceso"
    },
    {
        "numero": 86,
        "titulo": "Adivina con pistas",
        "enunciado": "Generar un número aleatorio entre 1 y 20 y dar pistas de mayor o menor.",
        "solucion": "Proceso Ejercicio86\n\n    Definir secreto, intento Como Entero\n\n    secreto <- Aleatorio(1, 20)\n\n    Repetir\n\n        Escribir \"Adivine el numero entre 1 y 20:\"\n\n        Leer intento\n\n        Si intento < secreto Entonces\n\n            Escribir \"Mas alto\"\n\n        SiNo\n\n            Si intento > secreto Entonces\n\n                Escribir \"Mas bajo\"\n\n            FinSi\n\n        FinSi\n\n    Hasta Que intento = secreto\n\n    Escribir \"Acertaste\"\n\nFinProceso"
    },
    {
        "numero": 87,
        "titulo": "Piedra, papel o tijera",
        "enunciado": "El usuario ingresa 1 piedra, 2 papel o 3 tijera. La computadora elige aleatoriamente.",
        "solucion": "Proceso Ejercicio87\n\n    Definir usuario, pc Como Entero\n\n    Escribir \"1. Piedra\"\n\n    Escribir \"2. Papel\"\n\n    Escribir \"3. Tijera\"\n\n    Leer usuario\n\n    pc <- Aleatorio(1, 3)\n\n \n\n    Escribir \"La computadora eligio: \", pc\n\n \n\n    Si usuario = pc Entonces\n\n        Escribir \"Empate\"\n\n    SiNo\n\n        Si (usuario = 1 Y pc = 3) O (usuario = 2 Y pc = 1) O (usuario = 3 Y pc = 2) Entonces\n\n            Escribir \"Ganaste\"\n\n        SiNo\n\n            Escribir \"Perdiste\"\n\n        FinSi\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 88,
        "titulo": "Sorteo de premio",
        "enunciado": "Generar un número aleatorio del 1 al 5 y mostrar el premio según salga.",
        "solucion": "Proceso Ejercicio88\n\n    Definir premio Como Entero\n\n    premio <- Aleatorio(1, 5)\n\n    Segun premio Hacer\n\n        1:\n\n            Escribir \"Ganaste un lapiz\"\n\n        2:\n\n            Escribir \"Ganaste un cuaderno\"\n\n        3:\n\n            Escribir \"Ganaste una taza\"\n\n        4:\n\n            Escribir \"Ganaste una mochila\"\n\n        5:\n\n            Escribir \"Ganaste un premio sorpresa\"\n\n    FinSegun\n\nFinProceso"
    },
    {
        "numero": 89,
        "titulo": "Contraseña aleatoria simple",
        "enunciado": "Generar una clave numérica aleatoria de 4 cifras entre 1000 y 9999.",
        "solucion": "Proceso Ejercicio89\n\n    Definir clave Como Entero\n\n    clave <- Aleatorio(1000, 9999)\n\n    Escribir \"Clave generada: \", clave\n\nFinProceso"
    },
    {
        "numero": 90,
        "titulo": "Llenar 5 casillas con números aleatorios",
        "enunciado": "Generar 5 números aleatorios entre 1 y 100 y mostrarlos.",
        "solucion": "Proceso Ejercicio90\n\n    Definir i, n Como Entero\n\n    Para i <- 1 Hasta 5 Hacer\n\n        n <- Aleatorio(1, 100)\n\n        Escribir \"Numero \", i, \": \", n\n\n    FinPara\n\nFinProceso"
    },
    {
        "numero": 91,
        "titulo": "Contar aleatorios pares",
        "enunciado": "Generar 10 números aleatorios entre 1 y 50 y contar cuántos son pares.",
        "solucion": "Proceso Ejercicio91\n\n    Definir i, n, contador Como Entero\n\n    contador <- 0\n\n    Para i <- 1 Hasta 10 Hacer\n\n        n <- Aleatorio(1, 50)\n\n        Escribir n\n\n        Si n MOD 2 = 0 Entonces\n\n            contador <- contador + 1\n\n        FinSi\n\n    FinPara\n\n    Escribir \"Cantidad de pares: \", contador\n\nFinProceso"
    },
    {
        "numero": 92,
        "titulo": "Promedio de aleatorios",
        "enunciado": "Generar 8 números aleatorios entre 1 y 10 y mostrar el promedio.",
        "solucion": "Proceso Ejercicio92\n\n    Definir i, n, suma, promedio Como Real\n\n    suma <- 0\n\n    Para i <- 1 Hasta 8 Hacer\n\n        n <- Aleatorio(1, 10)\n\n        Escribir n\n\n        suma <- suma + n\n\n    FinPara\n\n    promedio <- suma / 8\n\n    Escribir \"Promedio: \", promedio\n\nFinProceso"
    },
    {
        "numero": 93,
        "titulo": "Mayor de números aleatorios",
        "enunciado": "Generar 6 números aleatorios entre 1 y 99 y mostrar el mayor.",
        "solucion": "Proceso Ejercicio93\n\n    Definir i, n, mayor Como Entero\n\n    Para i <- 1 Hasta 6 Hacer\n\n        n <- Aleatorio(1, 99)\n\n        Escribir n\n\n        Si i = 1 O n > mayor Entonces\n\n            mayor <- n\n\n        FinSi\n\n    FinPara\n\n    Escribir \"Mayor: \", mayor\n\nFinProceso"
    },
    {
        "numero": 94,
        "titulo": "Simular nota aleatoria",
        "enunciado": "Generar una nota entera aleatoria entre 1 y 7 y decir si aprueba.",
        "solucion": "Proceso Ejercicio94\n\n    Definir nota Como Entero\n\n    nota <- Aleatorio(1, 7)\n\n    Escribir \"Nota: \", nota\n\n    Si nota >= 4 Entonces\n\n        Escribir \"Aprueba\"\n\n    SiNo\n\n        Escribir \"Reprueba\"\n\n    FinSi\n\nFinProceso"
    },
    {
        "numero": 95,
        "titulo": "Menú con validación",
        "enunciado": "Mostrar un menú y repetir hasta que se ingrese una opción válida del 1 al 4.",
        "solucion": "Proceso Ejercicio95\n\n    Definir opcion Como Entero\n\n    Repetir\n\n        Escribir \"1. Jugar\"\n\n        Escribir \"2. Cargar\"\n\n        Escribir \"3. Configuracion\"\n\n        Escribir \"4. Salir\"\n\n        Leer opcion\n\n    Hasta Que opcion >= 1 Y opcion <= 4\n\n \n\n    Escribir \"Opcion valida: \", opcion\n\nFinProceso"
    },
    {
        "numero": 96,
        "titulo": "Simulador de cajero",
        "enunciado": "Crear un menú con saldo inicial de 50000: 1 consultar saldo, 2 depositar, 3 girar, 4 salir.",
        "solucion": "Proceso Ejercicio96\n\n    Definir opcion Como Entero\n\n    Definir saldo, monto Como Real\n\n    saldo <- 50000\n\n \n\n    Repetir\n\n        Escribir \"1. Consultar saldo\"\n\n        Escribir \"2. Depositar\"\n\n        Escribir \"3. Girar\"\n\n        Escribir \"4. Salir\"\n\n        Leer opcion\n\n \n\n        Segun opcion Hacer\n\n            1:\n\n                Escribir \"Saldo actual: \", saldo\n\n            2:\n\n                Escribir \"Ingrese monto a depositar:\"\n\n                Leer monto\n\n                saldo <- saldo + monto\n\n            3:\n\n                Escribir \"Ingrese monto a girar:\"\n\n                Leer monto\n\n                Si monto <= saldo Entonces\n\n                    saldo <- saldo - monto\n\n                SiNo\n\n                    Escribir \"Saldo insuficiente\"\n\n                FinSi\n\n            4:\n\n                Escribir \"Saliendo...\"\n\n            De Otro Modo:\n\n                Escribir \"Opcion invalida\"\n\n        FinSegun\n\n    Hasta Que opcion = 4\n\nFinProceso"
    },
    {
        "numero": 97,
        "titulo": "Contar letras hasta escribir FIN",
        "enunciado": "Pedir palabras hasta escribir FIN y contar cuántas se ingresaron.",
        "solucion": "Proceso Ejercicio97\n\n    Definir palabra Como Cadena\n\n    Definir contador Como Entero\n\n    contador <- 0\n\n    Repetir\n\n        Escribir \"Ingrese una palabra (FIN para terminar):\"\n\n        Leer palabra\n\n        palabra <- Mayusculas(palabra)\n\n        Si palabra <> \"FIN\" Entonces\n\n            contador <- contador + 1\n\n        FinSi\n\n    Hasta Que palabra = \"FIN\"\n\n    Escribir \"Cantidad ingresada: \", contador\n\nFinProceso"
    },
    {
        "numero": 98,
        "titulo": "Suma de pares y de impares",
        "enunciado": "Pedir 10 números y sumar por separado pares e impares.",
        "solucion": "Proceso Ejercicio98\n\n    Definir i, n, sumaPares, sumaImpares Como Entero\n\n    sumaPares <- 0\n\n    sumaImpares <- 0\n\n \n\n    Para i <- 1 Hasta 10 Hacer\n\n        Escribir \"Ingrese un numero:\"\n\n        Leer n\n\n        Si n MOD 2 = 0 Entonces\n\n            sumaPares <- sumaPares + n\n\n        SiNo\n\n            sumaImpares <- sumaImpares + n\n\n        FinSi\n\n    FinPara\n\n \n\n    Escribir \"Suma pares: \", sumaPares\n\n    Escribir \"Suma impares: \", sumaImpares\n\nFinProceso"
    },
    {
        "numero": 99,
        "titulo": "Contador de aprobados y reprobados",
        "enunciado": "Pedir 8 notas y contar cuántas aprueban y cuántas reprueban.",
        "solucion": "Proceso Ejercicio99\n\n    Definir i, aprobados, reprobados Como Entero\n\n    Definir nota Como Real\n\n    aprobados <- 0\n\n    reprobados <- 0\n\n \n\n    Para i <- 1 Hasta 8 Hacer\n\n        Escribir \"Ingrese nota:\"\n\n        Leer nota\n\n        Si nota >= 4 Entonces\n\n            aprobados <- aprobados + 1\n\n        SiNo\n\n            reprobados <- reprobados + 1\n\n        FinSi\n\n    FinPara\n\n \n\n    Escribir \"Aprobados: \", aprobados\n\n    Escribir \"Reprobados: \", reprobados\n\nFinProceso"
    },
    {
        "numero": 100,
        "titulo": "Juego simple con vidas",
        "enunciado": "El usuario tiene 3 vidas para adivinar un número aleatorio entre 1 y 5.",
        "solucion": "Proceso Ejercicio100\n\n    Definir secreto, intento, vidas Como Entero\n\n    secreto <- Aleatorio(1, 5)\n\n    vidas <- 3\n\n \n\n    Mientras vidas > 0 Hacer\n\n        Escribir \"Adivine el numero entre 1 y 5:\"\n\n        Leer intento\n\n \n\n        Si intento = secreto Entonces\n\n            Escribir \"Ganaste\"\n\n            vidas <- 0\n\n        SiNo\n\n            vidas <- vidas - 1\n\n            Si vidas > 0 Entonces\n\n                Escribir \"Incorrecto. Te quedan \", vidas, \" vidas\"\n\n            SiNo\n\n                Escribir \"Perdiste. El numero era \", secreto\n\n            FinSi\n\n        FinSi\n\n    FinMientras\n\nFinProceso"
    }
]

def construir_ejercicio_desde_banco(item: Dict[str, Any]) -> Dict[str, Any]:
    numero = item["numero"]
    tema = detectar_tema_por_numero(numero)
    enunciado = item["enunciado"]
    solucion = limpiar_codigo_pseint(item["solucion"])

    if tema == "secuencial":
        return crear_ejercicio(
            f"banco_{numero:03d}",
            enunciado,
            "secuencial",
            ["escribir"],
            [],
            ["leer", "definir", "proceso", "finproceso"],
            ["si", "segun", "mientras", "repetir", "para", "aleatorio"],
            "Hazlo paso a paso, sin meter condiciones ni ciclos si no hacen falta.",
            solucion,
        )
    if tema == "condicional":
        return crear_ejercicio(
            f"banco_{numero:03d}",
            enunciado,
            "condicional",
            ["si", "escribir"],
            ["entonces"],
            ["leer", "definir", "sino", "finsi", "mod", "y", "o"],
            [],
            "Aquí necesitas una decisión. Si no hay decisión, no sirve de mucho, como varios jefes.",
            solucion,
        )
    if tema == "segun":
        return crear_ejercicio(
            f"banco_{numero:03d}",
            enunciado,
            "segun",
            ["segun", "escribir"],
            [],
            ["leer", "definir", "de otro modo", "finsegun", "mayusculas"],
            [],
            "Usa SEGUN para elegir entre opciones, letras, números o menús.",
            solucion,
        )
    if tema == "ciclos":
        return crear_ejercicio(
            f"banco_{numero:03d}",
            enunciado,
            "ciclo",
            ["escribir"],
            ["para", "mientras", "repetir"],
            ["leer", "definir", "finpara", "finmientras", "hasta que"],
            [],
            "Aquí toca repetir algo. La vida insiste y el código también.",
            solucion,
        )
    return crear_ejercicio(
        f"banco_{numero:03d}",
        enunciado,
        "azar",
        ["escribir", "aleatorio"],
        [],
        ["leer", "definir", "si", "segun", "para", "mientras", "repetir"],
        [],
        "Debes usar Aleatorio. Sí, el caos ahora es requisito formal.",
        solucion,
    )

# =========================
# BANCO DE EJERCICIOS
# =========================
ejercicios: Dict[str, List[Dict[str, Any]]] = {
    "secuencial": [],
    "condicional": [],
    "segun": [],
    "ciclos": [],
    "azar": [],
}

for item in BANCO_100:
    tema = detectar_tema_por_numero(item["numero"])
    ejercicio = construir_ejercicio_desde_banco(item)
    ejercicio["tema"] = tema
    ejercicio["numero_original"] = item["numero"]
    ejercicio["titulo_original"] = item["titulo"]
    ejercicios[tema].append(ejercicio)

# ejercicio_actual[canal_id] = {datos del ejercicio + autor_id}
ejercicio_actual: Dict[int, Dict[str, Any]] = {}

# intentos[(canal_id, user_id)] = numero_de_intentos
intentos: Dict[Tuple[int, int], int] = {}

# historial_usuario[user_id][tema] = {ids de ejercicios vistos}
historial_usuario: Dict[int, Dict[str, set]] = {}

# reinicio_pendiente[user_id] = tema
reinicio_pendiente: Dict[int, str] = {}

# =========================
# ENCUESTAS
# =========================
# encuesta_mensajes[message_id] = datos de la encuesta
encuesta_mensajes: Dict[int, Dict[str, Any]] = {}

# votos_encuesta[(message_id, user_id)] = indice_opcion
votos_encuesta: Dict[Tuple[int, int], int] = {}

TEMAS_ENCUESTA_VALIDOS = ["secuencial", "condicional", "segun", "ciclos", "azar"]

def obtener_historial_usuario(user_id: int, tema: str) -> set:
    if user_id not in historial_usuario:
        historial_usuario[user_id] = {}
    if tema not in historial_usuario[user_id]:
        historial_usuario[user_id][tema] = set()
    return historial_usuario[user_id][tema]

def elegir_ejercicio_no_repetido(user_id: int, tema: str) -> Optional[Dict[str, Any]]:
    vistos = obtener_historial_usuario(user_id, tema)
    disponibles = [e for e in ejercicios[tema] if e["id"] not in vistos]
    if not disponibles:
        return None
    return random.choice(disponibles).copy()

def marcar_ejercicio_como_visto(user_id: int, tema: str, ejercicio: Dict[str, Any]) -> None:
    vistos = obtener_historial_usuario(user_id, tema)
    vistos.add(ejercicio["id"])

def limpiar_ejercicio_de_canal(canal_id: int, user_id: int) -> None:
    intentos.pop((canal_id, user_id), None)
    if canal_id in ejercicio_actual and ejercicio_actual[canal_id].get("autor_id") == user_id:
        del ejercicio_actual[canal_id]

def obtener_ayuda_tema() -> str:
    return (
        "🧭 **Temas disponibles:**\n"
        "• `!ejercicio secuencial`\n"
        "• `!ejercicio condicional`\n"
        "• `!ejercicio segun`\n"
        "• `!ejercicio ciclos`\n"
        "• `!ejercicio azar`\n\n"
        "Extras:\n"
        "• `!saltar` cambia tu ejercicio actual\n"
        "• `!detener` cancela tu ejercicio actual\n"
        "• `!encuesta tema` crea una encuesta en el canal de encuestas\n"
        "• `!encuestas_temas` muestra los temas de encuestas"
    )

def revisar_respuesta(respuesta: str, ejercicio: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    texto = normalizar(respuesta)
    feedback: List[str] = []
    aciertos: List[str] = []
    puntos = 0

    for palabra in ejercicio.get("debe_tener", []):
        if contiene_palabra(texto, palabra):
            puntos += 1
            aciertos.append(f"Sí usaste '{palabra}'.")
        else:
            feedback.append(f"Te faltó usar '{palabra}'.")

    opciones = ejercicio.get("debe_tener_una", [])
    if opciones:
        ok, encontrada = contiene_alguna(texto, opciones)
        if ok:
            puntos += 1
            aciertos.append(f"Sí usaste una estructura válida: '{encontrada}'.")
        else:
            feedback.append("Te faltó usar al menos una de estas estructuras: " + ", ".join(opciones))

    for palabra in ejercicio.get("evitar", []):
        if contiene_palabra(texto, palabra):
            feedback.append(f"Ojo: en este ejercicio '{palabra}' no era necesario.")

    bonus = ["proceso", "finproceso", "finsi", "finmientras", "finpara", "finsegun", "hasta que", "definir", "aleatorio"]
    bonus_encontrados = sum(1 for palabra in bonus if contiene_palabra(texto, palabra))
    if bonus_encontrados >= 2:
        puntos += 1
        aciertos.append("Tu respuesta tiene parte de la estructura formal de PSeInt.")

    errores_reales = [f for f in feedback if "no era necesario" not in f]
    if puntos >= 4 and not errores_reales:
        estado = "🟢 PERFECTO"
    elif puntos >= 3:
        estado = "🔵 EXCELENTE"
    elif puntos >= 2:
        estado = "🟡 REGULAR"
    else:
        estado = "🔴 MAL"

    return estado, feedback, aciertos

def formatear_ejercicio(ejercicio: Dict[str, Any]) -> str:
    tipo = ejercicio["tipo_principal"].capitalize()
    obligatorias = ", ".join(ejercicio.get("debe_tener", []))
    alternativas = ejercicio.get("debe_tener_una", [])
    parte_alternativa = ""
    if alternativas:
        parte_alternativa = f"\n📌 Debes usar al menos una de estas: {', '.join(alternativas)}"

    return (
        f"🧠 **Ejercicio ({tipo})**\n"
        f"👉 {ejercicio['enunciado']}\n\n"
        f"📚 Tema: **{ejercicio['tema']}**\n"
        f"🔢 Número original del banco: **{ejercicio.get('numero_original', '?')}**\n"
        f"📚 Tipo principal: **{ejercicio['tipo_principal']}**\n"
        f"📌 Debes usar: {obligatorias if obligatorias else 'según el enunciado'}"
        f"{parte_alternativa}\n"
        f"💡 Pista: {ejercicio['pista']}\n\n"
        f"{obtener_ayuda_tema()}"
    )

def obtener_nombre_estado(estado: str) -> str:
    estado_normalizado = normalizar(estado)

    if "perfecto" in estado_normalizado:
        return "perfecto"
    if "excelente" in estado_normalizado or "bien" in estado_normalizado:
        return "excelente"
    if "regular" in estado_normalizado:
        return "regular"
    return "mal"

async def guardar_en_foro(
    bot,
    ejercicio: Dict[str, Any],
    respuesta: str,
    usuario,
    estado: str,
    intento_final: int = 1,
    solucion: str | None = None,
):
    canal_foro = bot.get_channel(FORO_ID)

    if canal_foro is None:
        print("No encontró el foro 💀")
        return

    nombre_estado = obtener_nombre_estado(estado)
    titulo = f"{estado} | {ejercicio['tema']} | {ejercicio['enunciado'][:35]}"

    contenido = f"""👤 Usuario: {usuario}
🔁 Intento: {intento_final}/3
🏷️ Categoría resultado: {nombre_estado.upper()}
🏷️ Tema: {ejercicio['tema']}
🏷️ Tipo principal: {ejercicio['tipo_principal']}
🔢 Número banco: {ejercicio.get('numero_original', '?')}

🧠 Ejercicio:
{ejercicio['enunciado']}

💻 Respuesta del usuario:
```text
{respuesta}
```

📌 Resultado:
{estado}
"""

    if solucion:
        contenido += f"""

🧩 Solución guía del bot:
```pseint
{solucion}
```
"""

    applied_tags = []
    try:
        tags_disponibles = getattr(canal_foro, "available_tags", [])
        for tag in tags_disponibles:
            if normalizar(tag.name) == nombre_estado:
                applied_tags.append(tag)
                break
    except Exception as e:
        print(f"No se pudieron leer las tags del foro: {e}")

    try:
        await canal_foro.create_thread(
            name=titulo,
            content=contenido,
            applied_tags=applied_tags
        )
    except TypeError:
        await canal_foro.create_thread(
            name=titulo,
            content=contenido
        )

def mutar_codigo_para_distractor(codigo: str, tema: str, semilla: int) -> str:
    rng = random.Random(semilla)
    falso = codigo

    reemplazos_comunes = [
        (" Hasta ", " HastaQue "),
        ("FinSi", "FinProceso"),
        ("Segun", "Si"),
        ("Aleatorio", "Azar"),
        ("FinPara", "FinProceso"),
        ("FinMientras", "FinProceso"),
        ("FinSegun", "FinProceso"),
        ("Entonces", "Hacer"),
    ]

    reemplazos_por_tema = {
        "secuencial": [
            ("Leer", "Escribir"),
            ("<-", "="),
            ("Definir", "Dimension"),
        ],
        "condicional": [
            ("Si", "Segun"),
            ("Entonces", "Hacer"),
            ("SiNo", "De Otro Modo"),
        ],
        "segun": [
            ("Segun", "Si"),
            ("De Otro Modo:", "SiNo"),
            ("FinSegun", "FinSi"),
        ],
        "ciclos": [
            ("Para", "Si"),
            ("Mientras", "Si"),
            ("Repetir", "Segun"),
            ("Hasta Que", "FinSi"),
        ],
        "azar": [
            ("Aleatorio", "Random"),
            ("Si", "Segun"),
            ("Segun", "Si"),
        ],
    }

    candidatos = reemplazos_por_tema.get(tema, []) + reemplazos_comunes
    rng.shuffle(candidatos)

    cambios = 0
    for antes, despues in candidatos:
        if antes in falso:
            falso = falso.replace(antes, despues, 1)
            cambios += 1
        if cambios >= 2:
            break

    if cambios == 0:
        falso = falso.replace("Proceso", "ProcesoMal", 1)

    return falso

def crear_distractores_unicos(correcta: str, tema: str, numero: int) -> List[str]:
    distractores: List[str] = []
    usados = {normalizar(correcta)}
    semillas_base = [numero * 11, numero * 17 + 3, numero * 23 + 5, numero * 29 + 7, numero * 31 + 9, numero * 37 + 11]

    for i, semilla in enumerate(semillas_base):
        candidato = limpiar_codigo_pseint(mutar_codigo_para_distractor(correcta, tema, semilla + i))
        clave = normalizar(candidato)
        if clave not in usados:
            distractores.append(candidato)
            usados.add(clave)
        if len(distractores) == 2:
            break

    contador = 0
    while len(distractores) < 2:
        contador += 1
        candidato = correcta.replace("FinProceso", f"FinProceso_{contador}", 1)
        clave = normalizar(candidato)
        if clave not in usados:
            distractores.append(candidato)
            usados.add(clave)

    return distractores


def crear_opciones_encuesta(item: Dict[str, Any]) -> Tuple[List[str], int]:
    tema = detectar_tema_por_numero(item["numero"])
    correcta = limpiar_codigo_pseint(item["solucion"])
    distractores = crear_distractores_unicos(correcta, tema, item["numero"])

    opciones = [
        {"texto": correcta, "correcta": True},
        {"texto": distractores[0], "correcta": False},
        {"texto": distractores[1], "correcta": False},
    ]
    random.shuffle(opciones)
    indice_correcto = next(i for i, op in enumerate(opciones) if op["correcta"])
    return [op["texto"] for op in opciones], indice_correcto

def obtener_item_para_encuesta(tema: str) -> Dict[str, Any]:
    tema = normalizar(tema)
    if tema in ("ciclo", "ciclos"):
        tema = "ciclos"
    if tema not in TEMAS_ENCUESTA_VALIDOS + ["aleatorio"]:
        tema = "secuencial"
    if tema == "aleatorio":
        tema = "azar"

    filtrados = [item for item in BANCO_100 if detectar_tema_por_numero(item["numero"]) == tema]
    return random.choice(filtrados)

def construir_resumen_votos(encuesta: Dict[str, Any]) -> str:
    nombres = encuesta.get("nombres_por_opcion", [[], [], []])
    lineas = []
    for i in range(3):
        lista = nombres[i]
        texto_nombres = ", ".join(lista) if lista else "Nadie todavía"
        lineas.append(f"**Opción {i+1}:** {len(lista)} voto(s)\n{texto_nombres}")
    return "\n\n".join(lineas)

async def registrar_log_encuesta(interaction: discord.Interaction, encuesta: Dict[str, Any], indice: int, fue_correcta: bool):
    canal_log = bot.get_channel(CANAL_RESULTADOS_ENCUESTAS_ID)
    if canal_log is None:
        return

    estado = "✅ Correcta" if fue_correcta else "❌ Incorrecta"
    try:
        await canal_log.send(
            f"🗳️ **Respuesta de encuesta**\n"
            f"👤 Usuario: {interaction.user}\n"
            f"📍 Canal: {interaction.channel.mention if interaction.channel else 'Desconocido'}\n"
            f"📚 Tema: **{encuesta['tema']}**\n"
            f"🔢 Ejercicio: **{encuesta['numero']}**\n"
            f"🧠 Enunciado: {encuesta['enunciado']}\n"
            f"🔘 Opción elegida: **{indice + 1}**\n"
            f"📌 Resultado: {estado}"
        )
    except Exception:
        pass


def construir_resumen_final_foro(encuesta: Dict[str, Any]) -> str:
    correcta = encuesta["correcta"]
    acertaron = encuesta["nombres_por_opcion"][correcta]
    fallaron = []
    for i, nombres in enumerate(encuesta["nombres_por_opcion"]):
        if i != correcta:
            fallaron.extend(nombres)

    lineas_opciones = []
    for i in range(3):
        nombres = encuesta["nombres_por_opcion"][i]
        texto_nombres = ", ".join(nombres) if nombres else "Nadie"
        marca = " ✅ Correcta" if i == correcta else " ❌ Incorrecta"
        lineas_opciones.append(
            f"**Opción {i+1}{marca}:** {len(nombres)} voto(s)\n{texto_nombres}"
        )

    texto_acertaron = ", ".join(acertaron) if acertaron else "Nadie acertó"
    texto_fallaron = ", ".join(fallaron) if fallaron else "Nadie falló"

    return (
        f"🗳️ **Resultado final de encuesta**\n"
        f"📚 Tema: **{encuesta['tema']}**\n"
        f"🔢 Ejercicio: **{encuesta['numero']}**\n"
        f"🧠 Título: **{encuesta['titulo']}**\n"
        f"📝 Enunciado: {encuesta['enunciado']}\n\n"
        f"✅ **Respuesta correcta:** Opción {correcta + 1}\n\n"
        f"🎯 **Quiénes acertaron ({len(acertaron)}):**\n{texto_acertaron}\n\n"
        f"💥 **Quiénes fallaron ({len(fallaron)}):**\n{texto_fallaron}\n\n"
        f"📊 **Desglose por opción:**\n\n" + "\n\n".join(lineas_opciones)
    )


async def publicar_resultado_encuesta_en_destino(encuesta: Dict[str, Any]):
    destino = bot.get_channel(CANAL_RESULTADOS_ENCUESTAS_ID)
    if destino is None:
        return

    titulo = f"Encuesta {encuesta['numero']} | Correcta: opción {encuesta['correcta'] + 1}"
    contenido = construir_resumen_final_foro(encuesta)

    try:
        if isinstance(destino, discord.ForumChannel):
            await destino.create_thread(name=titulo[:100], content=contenido)
        else:
            await destino.send(contenido)
    except Exception as e:
        print(f"No se pudo publicar el resultado final de la encuesta: {e}")


class EjercicioView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=1800)
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Estos botones son del ejercicio de otra persona. El desastre ya está suficientemente bien distribuido.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Saltar ejercicio", style=discord.ButtonStyle.primary, emoji="⏭️")
    async def saltar_boton(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal_id = interaction.channel.id
        if canal_id not in ejercicio_actual:
            await interaction.response.send_message("No hay un ejercicio activo para saltar.", ephemeral=True)
            return

        datos = ejercicio_actual[canal_id]
        if datos.get("autor_id") != interaction.user.id:
            await interaction.response.send_message("Ese ejercicio no es tuyo.", ephemeral=True)
            return

        tema = datos["tema"]
        marcar_ejercicio_como_visto(interaction.user.id, tema, datos)
        intentos.pop((canal_id, interaction.user.id), None)

        elegido = elegir_ejercicio_no_repetido(interaction.user.id, tema)
        if elegido is None:
            reinicio_pendiente[interaction.user.id] = tema
            del ejercicio_actual[canal_id]
            await interaction.response.send_message(
                f"📚 Ya no quedan más ejercicios de **{tema}**.\nEscribe `!reiniciar {tema}` si quieres volver a empezar.",
                ephemeral=False,
            )
            return

        elegido["autor_id"] = interaction.user.id
        ejercicio_actual[canal_id] = elegido
        intentos[(canal_id, interaction.user.id)] = 0

        await interaction.response.send_message(
            f"⏭️ Salté tu ejercicio anterior. Aquí va otro de **{tema}**:\n\n{formatear_ejercicio(elegido)}",
            view=EjercicioView(interaction.user.id),
        )

    @discord.ui.button(label="Detener ejercicio", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def detener_boton(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal_id = interaction.channel.id
        if canal_id not in ejercicio_actual:
            await interaction.response.send_message("No hay un ejercicio activo para detener.", ephemeral=True)
            return

        datos = ejercicio_actual[canal_id]
        if datos.get("autor_id") != interaction.user.id:
            await interaction.response.send_message("Ese ejercicio no es tuyo.", ephemeral=True)
            return

        limpiar_ejercicio_de_canal(canal_id, interaction.user.id)
        await interaction.response.send_message(
            "⏹️ Ejercicio detenido. Cuando quieras otro, usa `!ejercicio` con el tema que quieras.",
            ephemeral=False,
        )

class EncuestaView(discord.ui.View):
    def __init__(self, activa: bool = True):
        super().__init__(timeout=None)
        self.activa = activa
        if not activa:
            for child in self.children:
                child.disabled = True

    async def procesar_voto(self, interaction: discord.Interaction, indice_opcion: int):
        message = interaction.message
        if message is None:
            await interaction.response.send_message("No pude encontrar la encuesta. Discord y sus humores.", ephemeral=True)
            return

        encuesta = encuesta_mensajes.get(message.id)
        if encuesta is None:
            await interaction.response.send_message("Esta encuesta ya no está registrada.", ephemeral=True)
            return

        if not encuesta.get("activa", True):
            await interaction.response.send_message("⏰ Esta encuesta ya cerró. Tenían 3 minutos y, bueno, el tiempo sigue siendo cruel.", ephemeral=True)
            return

        clave = (message.id, interaction.user.id)
        if clave in votos_encuesta:
            voto_anterior = votos_encuesta[clave] + 1
            await interaction.response.send_message(
                f"❌ Ya votaste en esta encuesta con la opción **{voto_anterior}**. No puedes cambiar tu respuesta.",
                ephemeral=True,
            )
            return

        votos_encuesta[clave] = indice_opcion
        encuesta["votos"][indice_opcion].append(interaction.user.id)
        encuesta["nombres_por_opcion"][indice_opcion].append(str(interaction.user))

        fue_correcta = indice_opcion == encuesta["correcta"]
        resumen_votos = construir_resumen_votos(encuesta)

        embed = discord.Embed(
            title=f"🗳️ Encuesta PSeInt | Ejercicio {encuesta['numero']}",
            description=encuesta["enunciado"],
            color=discord.Color.blurple(),
        )
        embed.add_field(name="📚 Tema", value=encuesta["tema"], inline=True)
        embed.add_field(name="🧠 Título", value=encuesta["titulo"][:1024], inline=False)

        for i, opcion in enumerate(encuesta["opciones"], start=1):
            embed.add_field(
                name=f"💻 Opción {i}",
                value=f"```pseint\n{opcion[:950]}\n```",
                inline=False,
            )

        embed.add_field(
            name="👥 Quiénes votaron",
            value=resumen_votos[:1024],
            inline=False,
        )

        if encuesta.get("automatica"):
            embed.set_footer(text="Encuesta automática activa. Una vez que votas no puedes cambiar la opción. Duración total: 3 minutos.")
        else:
            embed.set_footer(text="Una vez que votas no puedes cambiar la opción.")

        await interaction.response.edit_message(embed=embed, view=self)
        await registrar_log_encuesta(interaction, encuesta, indice_opcion, fue_correcta)

        texto = "✅ Elegiste la correcta." if fue_correcta else f"❌ Esa no era. La correcta era la opción {encuesta['correcta'] + 1}."
        await interaction.followup.send(
            texto + " Ya quedó registrado y no puedes cambiar tu voto.",
            ephemeral=True,
        )

    @discord.ui.button(label="Opción 1", style=discord.ButtonStyle.primary, custom_id="encuesta_opcion_1")
    async def opcion_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.procesar_voto(interaction, 0)

    @discord.ui.button(label="Opción 2", style=discord.ButtonStyle.primary, custom_id="encuesta_opcion_2")
    async def opcion_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.procesar_voto(interaction, 1)

    @discord.ui.button(label="Opción 3", style=discord.ButtonStyle.primary, custom_id="encuesta_opcion_3")
    async def opcion_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.procesar_voto(interaction, 2)


async def cerrar_encuesta(message_id: int):
    encuesta = encuesta_mensajes.get(message_id)
    if encuesta is None or not encuesta.get("activa", True):
        return

    encuesta["activa"] = False
    canal = bot.get_channel(CANAL_ENCUESTAS_ID)
    if canal is None:
        return

    try:
        mensaje = await canal.fetch_message(message_id)
    except Exception:
        return

    resumen_votos = construir_resumen_votos(encuesta)
    correcta = encuesta["correcta"] + 1

    embed = discord.Embed(
        title=f"🗳️ Encuesta PSeInt | Ejercicio {encuesta['numero']} | Cerrada",
        description=encuesta["enunciado"],
        color=discord.Color.dark_gray(),
    )
    embed.add_field(name="📚 Tema", value=encuesta["tema"], inline=True)
    embed.add_field(name="🧠 Título", value=encuesta["titulo"][:1024], inline=False)

    for i, opcion in enumerate(encuesta["opciones"], start=1):
        embed.add_field(
            name=f"💻 Opción {i}",
            value=f"```pseint\n{opcion[:950]}\n```",
            inline=False,
        )

    embed.add_field(name="✅ Respuesta correcta", value=f"Opción {correcta}", inline=False)
    embed.add_field(name="👥 Resultado final", value=resumen_votos[:1024], inline=False)
    embed.set_footer(text="Encuesta cerrada. Ya no se puede votar.")

    await mensaje.edit(embed=embed, view=EncuestaView(activa=False))
    await canal.send(f"⏰ La encuesta del ejercicio **{encuesta['numero']}** terminó. La respuesta correcta era la **opción {correcta}**.")
    await publicar_resultado_encuesta_en_destino(encuesta)


async def publicar_encuesta(canal: discord.abc.Messageable, tema: str, automatica: bool = False, mencionar_todos: bool = False):
    item = obtener_item_para_encuesta(tema)
    opciones, correcta = crear_opciones_encuesta(item)

    embed = discord.Embed(
        title=f"🗳️ Encuesta PSeInt | Ejercicio {item['numero']}",
        description=item["enunciado"],
        color=discord.Color.blurple(),
    )
    embed.add_field(name="📚 Tema", value=tema, inline=True)
    embed.add_field(name="🧠 Título", value=item["titulo"], inline=False)

    for i, opcion in enumerate(opciones, start=1):
        embed.add_field(
            name=f"💻 Opción {i}",
            value=f"```pseint\n{opcion[:950]}\n```",
            inline=False,
        )

    embed.add_field(
        name="👥 Quiénes votaron",
        value="**Opción 1:** 0 voto(s)\nNadie todavía\n\n**Opción 2:** 0 voto(s)\nNadie todavía\n\n**Opción 3:** 0 voto(s)\nNadie todavía",
        inline=False,
    )

    if automatica:
        embed.set_footer(text="Encuesta automática. Tienen 3 minutos para responder. Una vez que votas no puedes cambiar la opción.")
    else:
        embed.set_footer(text="Elige una opción con los botones. No podrás cambiarla después.")

    contenido = None
    if mencionar_todos:
        contenido = "@everyone 🗳️ Nueva encuesta automática de PSeInt. Tienen **3 minutos** para responder."

    mensaje = await canal.send(content=contenido, embed=embed, view=EncuestaView())
    encuesta_mensajes[mensaje.id] = {
        "numero": item["numero"],
        "titulo": item["titulo"],
        "enunciado": item["enunciado"],
        "tema": tema,
        "opciones": opciones,
        "correcta": correcta,
        "votos": [[], [], []],
        "nombres_por_opcion": [[], [], []],
        "activa": True,
        "automatica": automatica,
    }

    if automatica:
        bot.loop.create_task(cerrar_encuesta_despues(mensaje.id, 180))

    return mensaje


async def cerrar_encuesta_despues(message_id: int, segundos: int):
    await asyncio.sleep(segundos)
    await cerrar_encuesta(message_id)


@tasks.loop(hours=5)
async def encuesta_automatica_loop():
    canal = bot.get_channel(CANAL_ENCUESTAS_ID)
    if canal is None:
        return

    tema = random.choice(TEMAS_ENCUESTA_VALIDOS)
    await publicar_encuesta(canal, tema, automatica=True, mencionar_todos=True)


@encuesta_automatica_loop.before_loop
async def before_encuesta_automatica_loop():
    await bot.wait_until_ready()
@bot.event
async def on_ready():
    total = sum(len(lista) for lista in ejercicios.values())
    bot.add_view(EncuestaView())
    if not encuesta_automatica_loop.is_running():
        encuesta_automatica_loop.start()
    print(f"Bot conectado como {bot.user}")
    print(f"Versión: {VERSION_BOT}")
    print(f"Ejercicios cargados: {total}")
    print("Vista persistente de encuestas registrada.")
    print("Loop de encuestas automáticas cada 5 horas iniciado.")

@bot.command()
async def hola(ctx):
    await ctx.send("Hola po 😎 soy tu bot de pseudocódigo")

@bot.command()
async def version(ctx):
    await ctx.send(
        f"🤖 **Versión del bot:** `{VERSION_BOT}`\n"
        "Ahora trae banco de 100 ejercicios, temas de SEGUN y AZAR, y encuestas con 3 botones, una sola respuesta por usuario y registro automático."
    )

@bot.command()
async def temas(ctx):
    await ctx.send(
        "📚 Temas disponibles:\n"
        "• secuencial\n"
        "• condicional\n"
        "• segun\n"
        "• ciclos\n"
        "• azar\n\n"
        "Ejemplos:\n"
        "• `!ejercicio secuencial`\n"
        "• `!ejercicio condicional`\n"
        "• `!ejercicio segun`\n"
        "• `!ejercicio ciclos`\n"
        "• `!ejercicio azar`\n\n"
        "Encuestas:\n"
        "• `!encuesta secuencial`\n"
        "• `!encuesta condicional`\n"
        "• `!encuesta segun`\n"
        "• `!encuesta ciclos`\n"
        "• `!encuesta azar`"
    )

@bot.command()
async def encuestas_temas(ctx):
    await ctx.send(
        "🗳️ **Temas de encuestas:**\n"
        "• secuencial\n"
        "• condicional\n"
        "• segun\n"
        "• ciclos\n"
        "• azar\n\n"
        "Usa por ejemplo: `!encuesta segun`"
    )

@bot.command()
async def cantidad(ctx):
    total = sum(len(lista) for lista in ejercicios.values())
    await ctx.send(
        "📦 Banco de ejercicios actual:\n"
        f"• Secuencial: {len(ejercicios['secuencial'])}\n"
        f"• Condicional: {len(ejercicios['condicional'])}\n"
        f"• Segun: {len(ejercicios['segun'])}\n"
        f"• Ciclos: {len(ejercicios['ciclos'])}\n"
        f"• Azar: {len(ejercicios['azar'])}\n"
        f"• Total: {total}"
    )

@bot.command(aliases=["ejercicios", "ej"])
async def ejercicio(ctx, tema: str = "secuencial"):
    if ctx.channel.id != CANAL_BOT_ID:
        await ctx.send("❌ Usa este comando en el canal del bot 😑")
        return

    tema = normalizar(tema)
    if tema == "ciclo":
        tema = "ciclos"
    if tema == "aleatorio":
        tema = "azar"

    if tema not in ejercicios:
        await ctx.send(
            "Ese tema no existe 😅 Usa `!temas` para ver los disponibles.\n\n"
            f"{obtener_ayuda_tema()}"
        )
        return

    user_id = ctx.author.id
    elegido = elegir_ejercicio_no_repetido(user_id, tema)

    if elegido is None:
        reinicio_pendiente[user_id] = tema
        await ctx.send(
            f"📚 Ya hiciste todos los ejercicios de **{tema}**.\n"
            f"Escribe `!reiniciar {tema}` si quieres volver a empezar esa categoría.\n"
            "El foro no se borrará. No hace falta empeorar el sistema."
        )
        return

    elegido["autor_id"] = user_id
    ejercicio_actual[ctx.channel.id] = elegido
    intentos[(ctx.channel.id, user_id)] = 0

    await ctx.send(formatear_ejercicio(elegido), view=EjercicioView(user_id))

@bot.command()
async def saltar(ctx):
    if ctx.channel.id != CANAL_BOT_ID:
        await ctx.send("❌ Usa este comando en el canal del bot 😑")
        return

    canal_id = ctx.channel.id
    if canal_id not in ejercicio_actual:
        await ctx.send("No hay un ejercicio activo para saltar. Pide uno con `!ejercicio`.")
        return

    datos = ejercicio_actual[canal_id]
    if datos.get("autor_id") != ctx.author.id:
        await ctx.send("❌ Solo quien pidió ese ejercicio puede saltarlo.")
        return

    tema = datos["tema"]
    marcar_ejercicio_como_visto(ctx.author.id, tema, datos)
    intentos.pop((canal_id, ctx.author.id), None)

    elegido = elegir_ejercicio_no_repetido(ctx.author.id, tema)
    if elegido is None:
        reinicio_pendiente[ctx.author.id] = tema
        del ejercicio_actual[canal_id]
        await ctx.send(
            f"📚 Ya no quedan más ejercicios de **{tema}**.\nUsa `!reiniciar {tema}` para empezar de nuevo."
        )
        return

    elegido["autor_id"] = ctx.author.id
    ejercicio_actual[canal_id] = elegido
    intentos[(canal_id, ctx.author.id)] = 0

    await ctx.send(
        f"⏭️ Ejercicio saltado. Aquí tienes otro de **{tema}**:\n\n{formatear_ejercicio(elegido)}",
        view=EjercicioView(ctx.author.id),
    )

@bot.command()
async def detener(ctx):
    if ctx.channel.id != CANAL_BOT_ID:
        await ctx.send("❌ Usa este comando en el canal del bot 😑")
        return

    canal_id = ctx.channel.id
    if canal_id not in ejercicio_actual:
        await ctx.send("No hay un ejercicio activo para detener.")
        return

    datos = ejercicio_actual[canal_id]
    if datos.get("autor_id") != ctx.author.id:
        await ctx.send("❌ Solo quien pidió ese ejercicio puede detenerlo.")
        return

    limpiar_ejercicio_de_canal(canal_id, ctx.author.id)
    await ctx.send("⏹️ Ejercicio detenido. Cuando quieras otro, usa `!ejercicio`.")

@bot.command()
async def reiniciar(ctx, tema: str):
    if ctx.channel.id != CANAL_BOT_ID:
        await ctx.send("❌ Usa este comando en el canal del bot 😑")
        return

    tema = normalizar(tema)
    if tema == "ciclo":
        tema = "ciclos"
    if tema == "aleatorio":
        tema = "azar"

    if tema not in ejercicios:
        await ctx.send("Ese tema no existe 😅 Usa `!temas` para ver los disponibles.")
        return

    user_id = ctx.author.id
    if user_id not in historial_usuario:
        historial_usuario[user_id] = {}

    historial_usuario[user_id][tema] = set()

    if reinicio_pendiente.get(user_id) == tema:
        del reinicio_pendiente[user_id]

    await ctx.send(
        f"♻️ Reinicié tu historial de **{tema}**.\n"
        "El foro quedó intacto. Milagro administrativo."
    )

@bot.command(aliases=["respuesta", "res"])
async def resolver(ctx, *, respuesta: str):
    if ctx.channel.id != CANAL_BOT_ID:
        await ctx.send("❌ Usa este comando en el canal del bot 😑")
        return

    if ctx.channel.id not in ejercicio_actual:
        await ctx.send("Primero pide un ejercicio con `!ejercicio` 😐")
        return

    datos = ejercicio_actual[ctx.channel.id]
    if datos.get("autor_id") != ctx.author.id:
        await ctx.send("❌ Solo quien pidió ese ejercicio puede resolverlo.")
        return

    clave_intento = (ctx.channel.id, ctx.author.id)
    intentos[clave_intento] = intentos.get(clave_intento, 0) + 1
    intento_actual = intentos[clave_intento]

    estado, feedback, aciertos = revisar_respuesta(respuesta, datos)

    mensaje = (
        f"📋 **Resultado:** {estado}\n"
        f"🔁 **Intento:** {intento_actual}/3\n"
        f"🏷️ **Tipo esperado:** {datos['tipo_principal']}\n"
        f"📚 **Tema:** {datos['tema']}\n"
        f"🔢 **Ejercicio banco:** {datos.get('numero_original', '?')}\n"
    )

    if aciertos:
        mensaje += "\n✅ **Lo que sí hiciste bien:**\n"
        for a in aciertos:
            mensaje += f"• {a}\n"

    if feedback:
        mensaje += "\n⚠️ **Correcciones:**\n"
        for f in feedback:
            mensaje += f"• {f}\n"
    else:
        mensaje += "\n✨ No encontré errores base en la estructura esperada. Una rareza estadística agradable.\n"

    solucion = None
    if intento_actual >= 3 and estado not in ["🟢 PERFECTO", "🔵 EXCELENTE"]:
        solucion = datos.get("solucion")
        if solucion:
            mensaje += (
                "\n🧩 **Ya vas en el tercer intento, así que te dejo una solución guía:**\n"
                f"```pseint\n{solucion}\n```"
            )

    await ctx.send(mensaje)

    estado_para_foro = estado
    if intento_actual >= 3 and estado not in ["🟢 PERFECTO", "🔵 EXCELENTE"]:
        estado_para_foro = "🔴 MAL"

    await guardar_en_foro(
        bot,
        datos,
        respuesta,
        ctx.author,
        estado_para_foro,
        intento_final=intento_actual,
        solucion=solucion,
    )

    if estado in ["🟢 PERFECTO", "🔵 EXCELENTE"]:
        marcar_ejercicio_como_visto(ctx.author.id, datos["tema"], datos)
        limpiar_ejercicio_de_canal(ctx.channel.id, ctx.author.id)
    elif intento_actual >= 3:
        marcar_ejercicio_como_visto(ctx.author.id, datos["tema"], datos)
        limpiar_ejercicio_de_canal(ctx.channel.id, ctx.author.id)

@bot.command()
async def encuesta(ctx, tema: str = "secuencial"):
    if CANAL_ENCUESTAS_ID == 0 or CANAL_RESULTADOS_ENCUESTAS_ID == 0:
        await ctx.send(
            "⚠️ Primero debes poner las IDs de `CANAL_ENCUESTAS_ID` y `CANAL_RESULTADOS_ENCUESTAS_ID` en el archivo.\n"
            "Sí, el bot no puede leer tu mente. Todavía."
        )
        return

    if ctx.channel.id != CANAL_ENCUESTAS_ID:
        await ctx.send("❌ Usa este comando en tu canal de **encuestas**.")
        return

    tema = normalizar(tema)
    if tema == "ciclo":
        tema = "ciclos"
    if tema == "aleatorio":
        tema = "azar"

    if tema not in TEMAS_ENCUESTA_VALIDOS:
        await ctx.send("❌ Ese tema no existe para encuestas. Usa `!encuestas_temas`.")
        return

    item = obtener_item_para_encuesta(tema)
    opciones, correcta = crear_opciones_encuesta(item)

    embed = discord.Embed(
        title=f"🗳️ Encuesta PSeInt | Ejercicio {item['numero']}",
        description=item["enunciado"],
        color=discord.Color.blurple(),
    )
    embed.add_field(name="📚 Tema", value=tema, inline=True)
    embed.add_field(name="🧠 Título", value=item["titulo"], inline=False)

    for i, opcion in enumerate(opciones, start=1):
        embed.add_field(
            name=f"💻 Opción {i}",
            value=f"```pseint\n{opcion[:950]}\n```",
            inline=False,
        )

    embed.add_field(
        name="👥 Quiénes votaron",
        value="**Opción 1:** 0 voto(s)\nNadie todavía\n\n**Opción 2:** 0 voto(s)\nNadie todavía\n\n**Opción 3:** 0 voto(s)\nNadie todavía",
        inline=False,
    )
    embed.set_footer(text="Elige una opción con los botones. No podrás cambiarla después.")

    mensaje = await ctx.send(embed=embed, view=EncuestaView())
    encuesta_mensajes[mensaje.id] = {
        "numero": item["numero"],
        "titulo": item["titulo"],
        "enunciado": item["enunciado"],
        "tema": tema,
        "opciones": opciones,
        "correcta": correcta,
        "votos": [[], [], []],
        "nombres_por_opcion": [[], [], []],
    }

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("No se encontró el token del bot. Configura la variable de entorno TOKEN.")

bot.run(TOKEN)
