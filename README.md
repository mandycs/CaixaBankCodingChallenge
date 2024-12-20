# Caixabank Coding Challenges

## Español

### Descripción General

Este repositorio alberga una serie de desafíos de programación inspirados en el entorno de Caixabank. A través de estos retos, se busca promover el pensamiento crítico, la resolución metódica de problemas y la mejora continua de las habilidades técnicas. En él se presentan soluciones con entornos dockerizados que permiten una ejecución más estandarizada, controlada y fácil de reproducir.

La variedad de desafíos abarca desde ejercicios introductorios hasta propuestas más complejas, siendo así de utilidad tanto para personas con conocimientos básicos de programación como para profesionales con experiencia. Además, la estandarización mediante contenedores Docker facilita la configuración del entorno de desarrollo y ejecución, agilizando la validación de las soluciones y asegurando su coherencia entre diferentes sistemas.

### Estructura del Repositorio

- **/Retos**:  
  Cada subdirectorio de esta carpeta corresponde a un desafío específico.  
  - **/Reto-1**, **/Reto-2**, etc.: En estos directorios se incluyen las descripciones detalladas de cada reto, las instrucciones para su resolución, así como el código fuente y posibles soluciones propuestas. En muchos casos se incluye un archivo `Dockerfile` y, en ocasiones, un `docker-compose.yml` que facilitan la ejecución del entorno completo.

- **/Documentación**:  
  Este directorio reúne información de referencia, guías de estilo, enlaces a fuentes externas, así como otros recursos que pueden ser de utilidad para comprender el contexto, las metodologías propuestas o los enfoques alternativos de solución.

- **/Herramientas**:  
  En esta sección se disponen scripts auxiliares, plantillas, utilidades de línea de comandos y otros componentes de apoyo para la ejecución y validación de los retos.

### Entorno Dockerizado

La mayor parte de las soluciones se han encapsulado en contenedores Docker, lo que permite:

- **Portabilidad**: Ejecutar el mismo entorno en distintos sistemas sin necesidad de ajustes específicos.
- **Reproducibilidad**: Garantizar que las dependencias y las versiones empleadas sean idénticas para todos los participantes.
- **Facilidad de despliegue**: Iniciar y detener los servicios asociados a cada reto de forma ágil, empleando Dockerfiles y/o `docker-compose`.

#### Cómo Ejecutar un Reto con Docker

1. **Clonar el repositorio**:  
   ```bash
   git clone https://github.com/mandycs/CaixaBankCodingChallenge.git
   cd CaixaBankCodingChallenge
   ```

2. **Examinar la carpeta del reto seleccionado**:  
   Dirígete al subdirectorio de un reto en particular, por ejemplo:  
   
3. **Construir la imagen Docker**:  
   ```bash
   docker-compose up --build
   ```

5. **Realizar pruebas y validaciones**:  
   Dentro del contenedor, o una vez el servicio esté disponible, siga las instrucciones del reto para validar el correcto funcionamiento de la solución.

### Contribuciones

Las contribuciones son bienvenidas. Puede ayudar mejorando la documentación, añadiendo nuevos retos, proponiendo soluciones alternativas o ampliando las herramientas disponibles.

1. Haga un *fork* de este repositorio.
2. Cree una rama descriptiva para su contribución.
3. Realice los cambios, pruébelos y, una vez satisfecho con los resultados, genere una *pull request* con una descripción detallada de las mejoras aportadas.

## English

### General Overview

This repository contains a collection of programming challenges inspired by Caixabank’s environment. These challenges are designed to foster critical thinking, systematic problem-solving, and continuous improvement of technical skills. The solutions are provided within Dockerized environments, ensuring standardized, controlled, and easily reproducible executions.

The range of challenges spans from introductory tasks to more complex proposals, proving useful for both beginners and experienced professionals. By leveraging Docker containers, the setup and runtime environment remain consistent, streamlining the verification of solutions and ensuring coherence across different operating systems.

### Repository Structure

- **/Retos (Challenges)**:  
  Each subdirectory corresponds to a specific challenge.  

- **/Documentación (Documentation)**:  
  This directory includes reference materials, style guides, external resource links, and other supportive texts. It offers insights into the context, methodologies, and alternative approaches to solving the presented problems.

- **/Herramientas (Tools)**:  
  This section stores auxiliary scripts, templates, command-line utilities, and other support components for executing and validating the challenges.

### Dockerized Environment

Most of the solutions are encapsulated within Docker containers, providing:

- **Portability**: Run the same environment on multiple systems without environment-specific tweaks.
- **Reproducibility**: Ensure that all dependencies and versions remain identical for every participant.
- **Deployment Ease**: Quickly start and stop services associated with each challenge using Dockerfiles and/or `docker-compose`.

#### Running a Challenge with Docker

1. **Clone the repository**:  
   ```bash
   git clone https://github.com/mandycs/CaixaBankCodingChallenge.git
   cd CaixaBankCodingChallenge
   ```

2. **Navigate to the chosen challenge’s folder**:  
   
3. **Build the Docker image** (if a `Dockerfile` is provided):  
  
   ```bash
   docker-compose up --build
   ```

5. **Testing and Validation**:  
   Inside the container or once the service is up, follow the challenge instructions to verify that the solution works as intended.

### Contributions

Contributions are welcome. Feel free to improve the documentation, add new challenges, propose alternative solutions, or enhance the available tools.

1. *Fork* this repository.
2. Create a descriptive branch for your contribution.
3. Implement and test your changes, then submit a *pull request* detailing the improvements you have made.
