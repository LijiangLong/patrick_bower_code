import argparse, torch, pdb
from VideoLoader import VideoLoader
import torchvision

parser = argparse.ArgumentParser()

parser.add_argument('--model', default='r3d', type=str, choices = ['r3d', 'mc3', 'r2plus1d'], 
					help='Architecture to use (r3d | mc3 | r2plus1d)')

parser.add_argument('--pretrain_path', type=str,
					help = 'Path of a previously trained model. If not provided, --model specifies the architecture to use')

parser.add_argument('--pretrained', default=True, type=bool,
					help='Use pretrained weights for model initialization')

parser.add_argument('--fine_tune', default=False, type=bool,
					help='Fine tune the pretrained weights through training')

parser.add_argument('--mode', default = 'train', type = str, choices = ['train', 'predict'], 
					help = 'Train a model or predict labels using previously created model')

parser.add_argument('--train_dir', default='/data/home/llong35/Temp/CichlidAnalyzer/__AnnotatedData/LabeledVideos/10classLabels/LabeledClips/training', type=str,
					help='path of the training directory. Assumed the directory will contain label/*mp4. Dataset must be training or testing')

parser.add_argument('--val_dir', default='/data/home/llong35/Temp/CichlidAnalyzer/__AnnotatedData/LabeledVideos/10classLabels/LabeledClips/validation', type=str,
					help='path of the validation directory. Assumed the directory will contain label/*mp4. Dataset must be training or testing')

parser.add_argument('--results', default='/data/home/llong35/data/12_16_2019', type=str,
					help='path of the results directory')

parser.add_argument('--num_classes', default=10, type=int,
					help='number of video categories')

parser.add_argument('--learning_rate', default=0.001, type=float,
					help='Learning rate of the model optimizer')

parser.add_argument('--momentum', default=0.9, type=float, 
					help='momentum of the model optimizer')

parser.add_argument('--weight_decay', default=1e-3, type=float,
					help='weight decay of the model optimizer')

parser.add_argument('--epochs', default=50, type=int,
					help='Number of epoch to train the model')

parser.add_argument('--batch_size', default=8, type=int,
					help='batch size for training and testing dataloader')

parser.add_argument('--num_workers', default=6, type=int,
					help='number of threads to use')
pdb.set_trace()
args = parser.parse_args()

if args.pretrain_path is not None:
	print('loading pretrained model {}'.format(args.pretrain_path))
	model = torch.load(args.pretrain_path)

else:
	if args.model == 'r3d':
		model = torchvision.models.video.r3d_18(pretrained=args.pre_trained, progress=True)

	elif args.model == 'mc3':
		model = torchvision.models.video.mc3_18(pretrained=args.pre_trained, progress=True)    

	elif args.model == 'r2plus1d':
		model = torchvision.models.video.r2plus1d_18(pretrained=args.pre_trained, progress=True)    

if args.mode == 'train':
	# Modifing the last layer according to our data
	model.fc = nn.Linear(in_features=512, out_features=args.num_classes, bias=True)

	if not args.fine_tune:
		for name,param in model.named_parameters():
			param.requires_grad = False

	# To parallalize the model. By default it uses all available gpu. 
	# Set visible devices using CUDA_VISIBLE_DEVICE
	device = torch.device("cuda:3")
	model.to(device)

	#model = model.cuda()
	#model = nn.DataParallel(model, device_ids=None)

	# Optimizer for the model
	optimizer = optim.SGD(model.parameters(), lr=args.learning_rate, momentum=args.momentum, weight_decay=args.weight_decay)

	# Load the trainset
	trainset = VideoLoader(args.train_dir, 'train', (90,112,112))
	trainset_loader = DataLoader(trainset, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, pin_memory = True)

	# Load the validation
	valset = VideoLoader(args.val_dir, 'val', (90,112,112))
	valset_loader = DataLoader(valset, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, pin_memory = True)

	optimizer = optim.SGD(model.parameters, lr=args.learning_rate, momentum=args.momentum, weight_decay=args.weight_decay)
	scheduler = lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=args.lr_patience)
	criterion = nn.CrossEntropyLoss()

	for epoch in range(args.epochs):
		model.train()
		start = time()
		iteration = 0
		avg_loss = 0
		correct = 0
		for batch_idx, (data, target, path) in enumerate(trainset_loader):
			#target = target.cuda(async = True)
			
			data = Variable(data)
			target = Variable(target)
			
			output = model(data)
			
			lossFunction = nn.CrossEntropyLoss()
			lossFunction = lossFunction.cuda()
			
			loss = lossFunction(output, target)
			avg_loss += loss

			optimizer.zero_grad()
			loss.backward()

			optimizer.step()
			
			if iteration % log_interval == 0:
				print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
					epoch, batch_idx * len(data), len(trainset_loader.dataset),
					100. * batch_idx / len(trainset_loader), loss.item()))
			iteration += 1
			pred = output.max(1, keepdim=True)[1] # get the index of the max log-probability
			correct += pred.eq(target.view_as(pred)).sum().item()
			
		end = time()
		print ('\nSummary: Epoch {}'.format(epoch))
		print('Time taken for this epoch: {:.2f}s'.format(end-start))
		print('Train set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)'.format(
		avg_loss/len(trainset_loader.dataset), correct, len(trainset_loader.dataset),
		100. * correct / len(trainset_loader.dataset)))
		
		# if epoch % args.save_interval == 0:
		# 	save_file_path = os.path.join(results, 'save_{}.pth'.format(epoch))
		# 	states = {
		# 		'epoch': epoch + 1,
		# 		'state_dict': model.state_dict(),
		# 		'optimizer': optimizer.state_dict(),
		# 	}
		# 	torch.save(states, save_file_path)
		# check_accuracy(epoch) # evaluate at the end of epoch
		model.val()
		start = time()
		iteration = 0
		avg_loss = 0
		correct = 0
		for batch_idx, (data, target, path) in enumerate(valset_loader):
			# target = target.cuda(async = True)

			data = Variable(data)
			target = Variable(target)

			output = model(data)

			lossFunction = nn.CrossEntropyLoss()
			lossFunction = lossFunction.cuda()

			loss = lossFunction(output, target)
			avg_loss += loss


			if iteration % log_interval == 0:
				print('Val Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
					epoch, batch_idx * len(data), len(trainset_loader.dataset),
						   100. * batch_idx / len(trainset_loader), loss.item()))
			iteration += 1
			pred = output.max(1, keepdim=True)[1]  # get the index of the max log-probability
			correct += pred.eq(target.view_as(pred)).sum().item()

		end = time()

		# print('Train set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)'.format(
		# 	avg_loss / len(trainset_loader.dataset), correct, len(trainset_loader.dataset),
		# 	100. * correct / len(trainset_loader.dataset)))
		# print('Val set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)'.format(
		# 	avg_loss / len(valset_loader.dataset), correct, len(trainset_loader.dataset),
		# 	100. * correct / len(trainset_loader.dataset)))
torch.cuda.empty_cache() # Clear cache after training
