import math
import torch
import random
from torch import autograd
from torch.nn import functional as F


def requires_grad(model, flag=True):
    for p in model.parameters():
        p.requires_grad = flag


def accumulate(model1, model2, decay=0.999):
    par1 = dict(model1.named_parameters())
    par2 = dict(model2.named_parameters())

    for k in par1.keys():
        par1[k].data.mul_(decay).add_(par2[k].data, alpha=1 - decay)


def d_logistic_loss(real_pred, fake_pred):
    real_loss = F.softplus(-real_pred)
    fake_loss = F.softplus(fake_pred)
    return real_loss.mean() + fake_loss.mean()


def g_nonsaturating_loss(fake_pred):
    loss = F.softplus(-fake_pred).mean()
    return loss


def g_path_regularize(fake_img, latents, mean_path_length, decay=0.01):
    noise = torch.randn_like(fake_img) / math.sqrt(fake_img.shape[2] * fake_img.shape[3])
    grad, = autograd.grad(outputs=(fake_img * noise).sum(), inputs=latents, create_graph=True)
    path_lengths = torch.sqrt(grad.pow(2).sum(2).mean(1))
    path_mean = mean_path_length + decay * (path_lengths.mean() - mean_path_length)
    path_penalty = (path_lengths - path_mean).pow(2).mean()
    return path_penalty, path_mean.detach(), path_lengths


def make_noise(batch, latent_dim, n_noise, device):
    if n_noise == 1:
        return torch.randn(batch, latent_dim, device=device)
    noises = torch.randn(n_noise, batch, latent_dim, device=device).unbind(0)
    return noises


def mixing_noise(batch, latent_dim, prob, device):
    if prob > 0 and random.random() < prob:
        return make_noise(batch, latent_dim, 2, device)
    else:
        return [make_noise(batch, latent_dim, 1, device)]


def set_grad_none(model, targets):
    for n, p in model.named_parameters():
        if n in targets:
            p.grad = None