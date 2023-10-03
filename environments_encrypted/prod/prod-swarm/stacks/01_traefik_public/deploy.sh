#!/bin/bash
exec nothelm run deploy --project-dir ../../../../../stack_templates/01_traefik_public -f values.yaml -f secrets/secret_values.yaml