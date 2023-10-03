#!/bin/bash
exec nothelm run deploy --project-dir ../../../../../stack_templates/02_monitoring -f values.yaml -f secrets/secret_values.yaml