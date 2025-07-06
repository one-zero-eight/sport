# Quality Attribute Scenarios

## PERFORMANCE EFFICIENCY

### Resource Utilization
Degree to which the amounts and types of resources used by a product or system, when performing its functions, meet requirements.

#### Memort test

**Source:** Students
**Stimulus:** 150 students try to check in at the training simultaneously
**Environment:** Sport website server under normal operating conditions
**Artifact:** Backend system for training check-in 
**Response:** Memory usage stays less than server capacity
**Response Measure:** Maximum memory usage during test: 2 GB

**Execution:**  
Simulate 150 users using a testing tool and check memory usage.

#### CPU test

**Source:** Students
**Stimulus:** 300 students browsing the sport website simultaneously
**Environment:** Sport website server under normal operating conditions
**Artifact:** Web server
**Response:** The page loads in acceptable time
**Response Measure:** CPU is not overloaded and the page loads under 2 seconds

**Execution:**  
Simulate 300 users using a testing tool and check CPU usage and page load time.
---

## MAINTAINABILITY

### Modularity
Degree to which a system or computer program is composed of discrete components such that a change to one component has minimal impact on other components.

#### Isolated Module Deployment

**Source:** Developer  
**Stimulus:** Check-in system update
**Environment:** Testing server  
**Artifact:** Backend  
**Response:** Only check-in systems updates
**Response Measure:** Other modules remain unchanged and database is untouched

**Execution:**  
Update check-in system and check if everything still operational.

---

## FLEXIBILITY

### Adaptability
Degree to which a product or system can effectively and efficiently be adapted for or transferred to different hardware, software or other operational or usage environments.

#### Environment Portability

**Source:** System administrator  
**Stimulus:** Installing website on another operation system
**Environment:** New operation system 
**Artifact:** Sport website
**Response:** Websites operates normally
**Response Measure:** Setup finishes without complications. Time taken is less than 1 hour.

**Execution:**  
Try installing the website on another operation system. For example: Windows -> Linux