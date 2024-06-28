from flask import Flask, request, jsonify
from trajectory.generator import generate_vehicle_trajectory

app = Flask(__name__)

@app.route('/trajectory', methods=['GET', 'POST'])
def trajectory():
    if request.method == 'GET':
        fence = request.args.get('fence')
        num_points = request.args.get('num_points', type=int, default=100)
        total_distance = request.args.get('total_distance', type=int, default=50000)
        error_margin = request.args.get('error_margin', type=float, default=0.00003)
    elif request.method == 'POST':
        data = request.json
        fence = data.get('fence')
        num_points = data.get('num_points', 100)
        total_distance = data.get('total_distance', 50000)
        error_margin = data.get('error_margin', 0.00003)

    if not fence:
        return jsonify({"error": "Fence parameter is required"}), 400

    try:
        trajectory = generate_vehicle_trajectory(fence, num_points, total_distance, error_margin)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"trajectory": trajectory})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5005)
