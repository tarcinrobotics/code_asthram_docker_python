from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
from PIL import Image
import re

app = Flask(__name__)
CORS(app)

@app.route('/execute', methods=['POST'])
def execute_code():
    data = request.json
    code = data.get('code')
    inputs = data.get('inputs', [])
    turtle_used = 'import turtle' in code

    # Store the code in a temporary file
    with open('temp_code.py', 'w') as f:
        f.write(code)

    print("Received code to execute:", code)
    print("Inputs:", inputs)

    try:
        if turtle_used:
            wrapped_code = (
                "import turtle\n"
                "from PIL import Image\n"
                "import os\n"
                "\n"
                "def run_turtle_code():\n"
                "    "
                + code.replace("\n", "\n    ") +
                "\n"
                "    screen = turtle.getscreen()\n"
                "    screen.getcanvas().postscript(file='turtle_output.ps')\n"
                "    turtle.bye()\n"
                "\n"
                "    img = Image.open('turtle_output.ps')\n"
                "    img.save('turtle_output.png')\n"
                "    os.remove('turtle_output.ps')\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    run_turtle_code()\n"
            )
            with open('temp_code.py', 'w') as f:
                f.write(wrapped_code)

            cmd = 'xvfb-run -a python3 temp_code.py'
        else:
            cmd = 'python3 temp_code.py'

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )

        output = []
        input_prompts = []
        input_iter = iter(inputs)

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            output.append(line)

            # Check for input prompt
            if re.search(r'Enter a text:', line):
                print(f"Input prompt detected: {line.strip()}")
                prompt = line.strip()
                input_prompts.append(prompt)
                try:
                    next_input = next(input_iter)
                except StopIteration:
                    process.kill()
                    print("Input required but no more inputs available.")
                    return jsonify({
                        'output': ''.join(output),
                        'input_prompts': input_prompts,
                        'input_required': True
                    })
                process.stdin.write(next_input + '\n')
                process.stdin.flush()

        combined_output = ''.join(output) + ''.join(process.stderr.readlines())
        print("Combined output:", combined_output)

        if input_prompts:
            print(f"Returning input prompts: {input_prompts}")
            return jsonify({
                'output': combined_output,
                'input_prompts': input_prompts,
                'input_required': True
            })

        if turtle_used and os.path.exists('turtle_output.png'):
            return send_file('turtle_output.png', mimetype='image/png')

        return jsonify({'output': combined_output, 'input_required': False})

    except subprocess.TimeoutExpired:
        process.kill()
        print("Execution timed out.")
        return jsonify({'output': 'Execution timed out.'})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'output': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
