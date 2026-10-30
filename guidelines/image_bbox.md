# Vehicle Bounding Box Annotation Guidelines

This project involves labeling vehicles in images using bounding boxes.
The annotations will be used for training computer vision models.

**Label Studio project:** Vehicles - Image Data Annotation
**Image source:** Pexels / Kaggle (see DATASETS.md)

## Label Classes

| Label | Includes | Does NOT include |
|---|---|---|
| **Car** | Sedans, hatchbacks, SUVs, pickup trucks, minivans | Delivery/cargo vans, trucks |
| **Bus** | City buses, coaches, school buses, minibuses | Minivans |
| **Truck** | Box trucks, lorries, semi-trucks, dump trucks, delivery/cargo vans | Pickup trucks (→ Car) |
| **Motorcycle** | Motorcycles, scooters, mopeds | Bicycles |

* **Motorcycle with rider:** one box around the motorcycle and rider together.
* **Semi-truck with trailer:** one box covering the cab and trailer together.
* **Parked vehicles:** label them too.
* Do not label bicycles, trains, or vehicles in posters, billboards or screens.

## Attributes
For every labeled vehicle, you MUST answer both attributes. Do not leave them blank.

### 1. Occlusion
Is the vehicle partially blocked by another object in the scene?
* **Yes**: about 10% or more of the vehicle is hidden by another object
  (another vehicle, person, pole, tree, sign, building).
* **No**: the vehicle is fully visible, or less than 10% is hidden.

### 2. Truncation
Is the vehicle cut off by the edge of the image?
* **Yes**: part of the vehicle is outside the image (left, right, top or bottom edge).
* **No**: the whole vehicle is inside the image.

### Attribute notes
* A vehicle can be both occluded and truncated. Answer each question separately.
* Occlusion is about **other objects**; truncation is about the **image edge**.
* **Motorcycle rider** is part of the Motorcycle box, so it does NOT count as occlusion.
* **Truck trailer** is part of the Truck box, so it does NOT count as occlusion.

## Annotation Rules

### 1. Label only visible parts
* Draw boxes only around the visible portion of the vehicle.
* Do not estimate or include hidden parts.

### 2. Do not label uncertain objects
* If you are not sure the object is a vehicle, do not label it.
* Skip vehicles smaller than about 10×10 pixels.
* If you're unsure between two classes, choose the closest one and note it under "Edge cases".

### 3. Tight bounding boxes
* Boxes must closely fit the visible outline of the vehicle.
* Avoid large empty spaces inside the box.
* Do not cut off visible vehicle parts.

### 4. Occlusion handling
* If a vehicle is partially blocked, still annotate it.
* Only box the visible part.

### 5. Overlapping vehicles
* Each vehicle gets its own box, even when boxes overlap.

### 6. Reflections, shadows and glass
* Do not label reflections (glass, water, mirrors).
* Do not label shadows.
* Do not label vehicles seen through glass (windows, shop glass, transparent barriers).
* Only label vehicles directly visible in the actual scene.

## Edge cases found during annotation
* (add notes here as you annotate, for example "food truck labeled as Truck")
