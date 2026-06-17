#!/usr/bin/bash

# Default values for parameters
DEFAULT_DIRECTORY=/home/ubuntu/prompt-engineering-workshop/app
DEFAULT_PORT=8084
DEFAULT_APP_FILE="Home.py"
DEFAULT_REQUIREMENTS_FILE="requirements.txt"
DEFAULT_APP_NAME=""  # Will be derived from APP_FILE if not provided
DEFAULT_APP_USER=""  # Current user by default
DEFAULT_PYTHON="python3.12"  # Python version to use for venv

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --directory|-d)
            DIRECTORY="$2"
            shift 2
            ;;
        --port|-p)
            PORT="$2"
            shift 2
            ;;
        --app|-a)
            APP_FILE="$2"
            shift 2
            ;;
        --app-name|-n)
            APP_NAME="$2"
            shift 2
            ;;
        --app-user|-u)
            APP_USER="$2"
            shift 2
            ;;
        --requirements|-r)
            REQUIREMENTS_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --directory, -d    Directory containing the application (default: $DEFAULT_DIRECTORY)"
            echo "  --port, -p         Port to run the application on (default: $DEFAULT_PORT)"
            echo "  --app, -a          Application file to run (default: $DEFAULT_APP_FILE)"
            echo "  --app-name, -n     Custom application name for logs (default: derived from app file)"
            echo "  --app-user, -u     User to run the application as (default: current user)"
            echo "  --requirements, -r Requirements file (default: $DEFAULT_REQUIREMENTS_FILE)"
            echo "  --help, -h         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown parameter: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Apply default values if parameters were not provided
DIRECTORY=${DIRECTORY:-$DEFAULT_DIRECTORY}
PORT=${PORT:-$DEFAULT_PORT}
APP_FILE=${APP_FILE:-$DEFAULT_APP_FILE}
REQUIREMENTS_FILE=${REQUIREMENTS_FILE:-$DEFAULT_REQUIREMENTS_FILE}
APP_USER=${APP_USER:-$DEFAULT_APP_USER}
PYTHON=${PYTHON:-$DEFAULT_PYTHON}

# Define absolute paths
APP_PATH="${DIRECTORY}/${APP_FILE}"

# Set APP_NAME if not provided
if [ -z "$APP_NAME" ]; then
    APP_NAME=$(basename "${APP_FILE}" .py)
fi

# Check if we're root and APP_USER is specified
if [ "$(id -u)" -eq 0 ] && [ -n "$APP_USER" ]; then
    # Check if the specified user exists
    if ! id -u "$APP_USER" >/dev/null 2>&1; then
        echo "Error: User $APP_USER does not exist"
        exit 1
    fi
fi

# Derived values
VENV_PATH="${DIRECTORY}/.venv"
REQUIREMENTS_PATH="${DIRECTORY}/${REQUIREMENTS_FILE}"
PID_FILE="${DIRECTORY}/pid"
LOG_DIR="${DIRECTORY}/log"
LOG_FILE="${LOG_DIR}/${APP_NAME}.log"

# Create log directory and ensure permissions
mkdir -p "$LOG_DIR" || { echo "Failed to create log directory"; exit 1; }

# Ensure proper ownership of directories if running as root and APP_USER is specified
if [ "$(id -u)" -eq 0 ] && [ -n "$APP_USER" ]; then
    chown -R "$APP_USER" "$LOG_DIR" || { echo "Failed to change ownership of log directory"; exit 1; }
    touch "$LOG_FILE" 2>/dev/null || true
    chown "$APP_USER" "$LOG_FILE" 2>/dev/null || true
fi

# Setup logging function
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Function to run a command as the specified user
run_as_user() {
    if [ "$(id -u)" -eq 0 ] && [ -n "$APP_USER" ]; then
        sudo -u "$APP_USER" "$@"
    else
        "$@"
    fi
}

# Change to the target directory
cd "$DIRECTORY" || { log "ERROR" "Failed to change to directory $DIRECTORY"; exit 1; }
log "INFO" "Working in $(pwd)"

# Function to check if port is in use and kill the process if needed
check_port_and_kill() {
    if command -v netstat &> /dev/null; then
        PORT_PID=$(netstat -tuln | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1)
        if [ -n "$PORT_PID" ]; then
            log "WARNING" "Port $PORT is in use by process $PORT_PID. Killing..."
            if [ "$(id -u)" -eq 0 ]; then
                kill -9 "$PORT_PID" 2>/dev/null
            else
                # Check if we have permission to kill the process
                if ps -o user= -p "$PORT_PID" 2>/dev/null | grep -q "^$(whoami)$"; then
                    kill -9 "$PORT_PID" 2>/dev/null
                else
                    log "ERROR" "Cannot kill process $PORT_PID - insufficient permissions"
                    exit 1
                fi
            fi
            sleep 2
        fi
    elif command -v lsof &> /dev/null; then
        PORT_PID=$(lsof -i:"$PORT" -t 2>/dev/null)
        if [ -n "$PORT_PID" ]; then
            log "WARNING" "Port $PORT is in use by process $PORT_PID. Killing..."
            if [ "$(id -u)" -eq 0 ]; then
                kill -9 "$PORT_PID" 2>/dev/null
            else
                # Check if we have permission to kill the process
                if ps -o user= -p "$PORT_PID" 2>/dev/null | grep -q "^$(whoami)$"; then
                    kill -9 "$PORT_PID" 2>/dev/null
                else
                    log "ERROR" "Cannot kill process $PORT_PID - insufficient permissions"
                    exit 1
                fi
            fi
            sleep 2
        fi
    fi
}

# Function to check if previous app instance is running
check_previous_app() {
    if [ -f "$PID_FILE" ]; then
        PREV_PID=$(cat "$PID_FILE")
        if ps -p "$PREV_PID" > /dev/null 2>&1; then
            log "WARNING" "Previous application instance running with PID $PREV_PID. Killing..."
            if [ "$(id -u)" -eq 0 ]; then
                kill -9 "$PREV_PID" 2>/dev/null
            else
                # Check if we have permission to kill the process
                if ps -o user= -p "$PREV_PID" 2>/dev/null | grep -q "^$(whoami)$"; then
                    kill -9 "$PREV_PID" 2>/dev/null
                else
                    log "ERROR" "Cannot kill process $PREV_PID - insufficient permissions"
                    exit 1
                fi
            fi
            sleep 2
        else
            log "INFO" "Previous PID file exists but process is not running. Cleaning up..."
        fi
    fi
}

# Function to create and set up virtual environment
setup_venv() {
    log "INFO" "Creating virtual environment with $PYTHON..."
    run_as_user "$PYTHON" -m venv "$VENV_PATH" || { log "ERROR" "Failed to create virtual environment"; return 1; }
    
    # Activate virtual environment - must be done in the current shell
    source "${VENV_PATH}/bin/activate" || { log "ERROR" "Failed to activate virtual environment"; return 1; }
    
    log "INFO" "Upgrading pip..."
    run_as_user pip install -U pip >> "$LOG_FILE" 2>&1
    
    log "INFO" "Installing dependencies from $REQUIREMENTS_PATH..."
    run_as_user pip install -r "$REQUIREMENTS_PATH" >> "$LOG_FILE" 2>&1 || { log "ERROR" "Failed to install requirements"; return 1; }
    
    return 0
}

# Function to activate and update existing environment
update_venv() {
    log "INFO" "Using existing virtual environment..."
    source "${VENV_PATH}/bin/activate" || { log "ERROR" "Failed to activate virtual environment"; return 1; }
    
    log "INFO" "Updating dependencies from $REQUIREMENTS_PATH..."
    run_as_user pip install -r "$REQUIREMENTS_PATH" >> "$LOG_FILE" 2>&1 || { log "ERROR" "Failed to update requirements"; return 1; }
    
    return 0
}

# Function to rebuild the virtual environment if needed
rebuild_venv() {
    log "INFO" "Rebuilding virtual environment..."
    # Kill any running processes
    if [ -f "$PID_FILE" ]; then
        PREV_PID=$(cat "$PID_FILE")
        if ps -p "$PREV_PID" > /dev/null 2>&1; then
            if [ "$(id -u)" -eq 0 ]; then
                kill -9 "$PREV_PID" 2>/dev/null
            else
                # Check if we have permission to kill the process
                if ps -o user= -p "$PREV_PID" 2>/dev/null | grep -q "^$(whoami)$"; then
                    kill -9 "$PREV_PID" 2>/dev/null
                else
                    log "ERROR" "Cannot kill process $PREV_PID - insufficient permissions"
                    exit 1
                fi
            fi
        fi
    fi
    
    # Remove existing venv directory
    rm -rf "$VENV_PATH" || { log "ERROR" "Failed to remove old virtual environment"; return 1; }
    
    # Setup new venv
    setup_venv
    return $?
}

# Function to start the application
start_app() {
    log "INFO" "Starting Streamlit application on port $PORT..."
    
    # Ensure permissions for log file
    if [ "$(id -u)" -eq 0 ] && [ -n "$APP_USER" ]; then
        touch "$LOG_FILE" 2>/dev/null || true
        chown "$APP_USER" "$LOG_FILE" 2>/dev/null || true
    fi
    
    if [ "$(id -u)" -eq 0 ] && [ -n "$APP_USER" ]; then
        # Start as the specified user
        su -c "nohup \"${VENV_PATH}/bin/streamlit\" run \"$APP_PATH\" --server.port \"$PORT\" >> \"$LOG_FILE\" 2>&1 &" "$APP_USER"
        # Get PID of the last background process run by the specified user
        APP_PID=$(ps -u "$APP_USER" -o pid,comm | grep streamlit | awk '{print $1}' | head -n 1)
    else
        # Start as current user
        nohup "${VENV_PATH}/bin/streamlit" run "$APP_PATH" --server.port "$PORT" >> "$LOG_FILE" 2>&1 &
        APP_PID=$!
    fi
    
    if [ -z "$APP_PID" ]; then
        log "ERROR" "Failed to get PID of the application"
        return 1
    fi
    
    # Store the PID
    echo "$APP_PID" > "$PID_FILE"
    log "INFO" "Application started with PID $APP_PID"
    
    # Wait a moment to ensure the app is starting correctly
    sleep 3
    
    # Check if the application is running
    if ps -p "$APP_PID" > /dev/null; then
        log "INFO" "Application successfully started on port $PORT"
        
        # Check if port is actually in use
        if command -v netstat &> /dev/null; then
            if netstat -tuln | grep -q ":$PORT "; then
                log "INFO" "Confirmed: Port $PORT is now active"
                return 0
            else
                log "WARNING" "Application started but port $PORT is not yet active"
                return 1
            fi
        elif command -v lsof &> /dev/null; then
            if lsof -i:"$PORT" > /dev/null; then
                log "INFO" "Confirmed: Port $PORT is now active"
                return 0
            else
                log "WARNING" "Application started but port $PORT is not yet active"
                return 1
            fi
        fi
    else
        log "ERROR" "Application failed to start. Check logs for details."
        return 1
    fi
}

# Print the configuration
log "INFO" "Configuration:"
log "INFO" "  Directory: $DIRECTORY"
log "INFO" "  Port: $PORT"
log "INFO" "  Application file: $APP_PATH"
log "INFO" "  Application name: $APP_NAME"
log "INFO" "  Requirements file: $REQUIREMENTS_PATH"
log "INFO" "  Log file: $LOG_FILE"
if [ -n "$APP_USER" ]; then
    log "INFO" "  Running as user: $APP_USER"
else
    log "INFO" "  Running as current user: $(whoami)"
fi

# Main workflow

# 1. Check if port in use, if yes kill the process
check_port_and_kill

# Check if previous app is running based on PID file
check_previous_app

# Ensure proper ownership of directories if running as root and APP_USER is specified
if [ "$(id -u)" -eq 0 ] && [ -n "$APP_USER" ]; then
    chown -R "$APP_USER" "$DIRECTORY" || { log "ERROR" "Failed to change ownership of directory"; exit 1; }
fi

# 2. Setup or update the venv
if [ -d "$VENV_PATH" ]; then
    # 3. Update existing venv
    if ! update_venv; then
        # 4. Rebuild if update fails
        log "WARNING" "Virtual environment update failed. Rebuilding..."
        rebuild_venv || { log "ERROR" "Failed to rebuild virtual environment"; exit 1; }
    fi
else
    # Fresh setup
    setup_venv || { log "ERROR" "Failed to setup virtual environment"; exit 1; }
fi

# Start the application
if ! start_app; then
    # 4. If application fails to start, rebuild the venv
    log "WARNING" "Application failed to start. Rebuilding virtual environment..."
    rebuild_venv || { log "ERROR" "Failed to rebuild virtual environment"; exit 1; }
    
    # Try starting the app again
    start_app || { log "ERROR" "Application failed to start even after rebuilding venv"; exit 1; }
fi

# 5. Final check if application is running
if [ -f "$PID_FILE" ]; then
    CURR_PID=$(cat "$PID_FILE")
    if ps -p "$CURR_PID" > /dev/null; then
        log "INFO" "Application is running successfully with PID $CURR_PID"
    else
        log "ERROR" "Application is not running!"
        exit 1
    fi
else
    log "ERROR" "PID file not found!"
    exit 1
fi

# Deactivate the virtual environment
deactivate

