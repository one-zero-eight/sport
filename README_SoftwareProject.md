<br />
<div align="center">
  <a href="https://innohassle.ru">
    <img alt="InNoHassle" height="200px" src="https://raw.githubusercontent.com/one-zero-eight/design/212a5c06590c4d469a0a894481c09915a4b1735f/logo/ing-white-outline-transparent.svg">
  </a>

  <h1 align="center">InnoNoHassle: Sport &ndash; Backend</h1>
  <p align="center">
    <p align="center">
    Backend of the sport page in the InnoNoHassle ecosystem. <br />
    <a href="https://...">Deployed Product</a>
    &middot;
    <a href="https://...">Demo Video</a>
  </p>
</div>

## About The Project
...

### Goals
- ...
- ...

### Roadmap

- [ ] ...
- [ ] ...

### Context diagram

This diagram shows the high-level context of the project, including key stakeholders and external systems interacting with the core application.

```mermaid
graph TB
    subgraph Stakeholders
        A[Sport website administrator]
        B[Students]
        C[Trainers]
    end

    subgraph External Systems
        SSO[University SSO Provider]
        Mail[University Email Server]
    end

    subgraph Core System
        CSWS[Website for students]
        CSACP[Admin control page]
    end

    A --> CSWS
    B --> CSWS
    C --> CSWS
    A --> CSACP


    CSWS --> SSO
    CSWS --> Mail
    CSACP --> Mail
```

## Getting Started

This is an example of how you may give instructions on setting up your project locally. To get a local copy up and running follow these simple example steps.

### Prerequisites
...

### Installation
...

### Usage
...

## Contributing
...

## License
...










